"""Hot mic panel for hands-free voice-to-tmux integration."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QTimer, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QFrame,
)

from ..audio.vad_recorder import VADRecorder
from ..config import AppConfig
from ..integrations.claude_grid import ClaudeGridBridge
from ..integrations.session_matcher import SessionMatcher
from ..stt import Transcriber, TranscriberError
from .widgets import LEDIndicator, LevelMeter, SessionSelector


class _TranscribeWorker(QThread):
    """Background worker for transcribing a VAD segment."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, transcriber: Transcriber, audio_path: Path):
        super().__init__()
        self.transcriber = transcriber
        self.audio_path = audio_path

    def run(self):
        try:
            transcript = self.transcriber.transcribe(self.audio_path)
            self.finished.emit(transcript)
        except TranscriberError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(f"Unexpected error: {e}")
        finally:
            # Clean up segment file
            try:
                self.audio_path.unlink(missing_ok=True)
            except Exception:
                pass


class HotMicPanel(QWidget):
    """Hot mic panel: continuous listening, transcription, and tmux dispatch.

    Signals:
        active_changed(bool): Emitted when hot mic is toggled on/off.
    """

    active_changed = Signal(bool)

    def __init__(
        self,
        config: AppConfig,
        transcriber: Transcriber,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)

        self._config = config
        self._transcriber = transcriber
        self._bridge = ClaudeGridBridge()
        self._matcher = SessionMatcher(min_confidence=config.hotmic.match_confidence)
        self._vad: Optional[VADRecorder] = None
        self._worker: Optional[_TranscribeWorker] = None
        self._is_active = False

        # Accumulation buffer for stop-word mode
        self._accumulated_text: list[str] = []

        # Accumulation timeout — discard buffer after prolonged silence
        self._accumulation_timer = QTimer(self)
        self._accumulation_timer.setSingleShot(True)
        self._accumulation_timer.timeout.connect(self._on_accumulation_timeout)

        # Session refresh timer
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_sessions)
        self._refresh_timer.setInterval(5000)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #2a2a32; max-height: 1px;")
        layout.addWidget(divider)

        # Header row: label + toggle button
        header = QHBoxLayout()
        header.setSpacing(10)

        section_label = QLabel("HOT MIC")
        section_label.setObjectName("sectionLabel")
        header.addWidget(section_label)

        header.addStretch()

        self._toggle_btn = QPushButton("OFF")
        self._toggle_btn.setFixedSize(56, 28)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._on_toggle)
        self._update_toggle_style(False)
        header.addWidget(self._toggle_btn)

        layout.addLayout(header)

        # Session pills
        self._session_selector = SessionSelector()
        self._session_selector.session_clicked.connect(self._on_session_selected)
        layout.addWidget(self._session_selector)

        # Level meter
        self._level_meter = LevelMeter()
        self._level_meter.setFixedHeight(14)
        layout.addWidget(self._level_meter)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self._status_led = LEDIndicator()
        status_row.addWidget(self._status_led)

        self._status_label = QLabel("Inactive")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setStyleSheet("""
            font-size: 11px;
            color: #808088;
            padding: 4px 8px;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #151518, stop:1 #1a1a1e
            );
            border: 1px solid #2a2a30;
            border-radius: 4px;
        """)
        status_row.addWidget(self._status_label, 1)

        layout.addLayout(status_row)

        # Transcript preview
        self._preview = QTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMaximumHeight(80)
        self._preview.setPlaceholderText("Hot mic transcript preview...")
        self._preview.setStyleSheet("""
            QTextEdit {
                background-color: #141418;
                border: 1px solid #2a2a32;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
                color: #b0b0b8;
            }
        """)
        layout.addWidget(self._preview)

        # Start hidden/disabled
        self._set_panel_enabled(False)

    @property
    def is_active(self) -> bool:
        return self._is_active

    def update_config(self, config: AppConfig, transcriber: Transcriber) -> None:
        """Update config and transcriber after settings change."""
        self._config = config
        self._transcriber = transcriber
        self._matcher = SessionMatcher(min_confidence=config.hotmic.match_confidence)

    def toggle(self) -> None:
        """Toggle hot mic on/off programmatically."""
        self._on_toggle()

    def stop(self) -> None:
        """Force-stop hot mic (e.g. on window close)."""
        if self._is_active:
            self._deactivate()

    def _on_toggle(self) -> None:
        if self._is_active:
            self._deactivate()
        else:
            self._activate()

    def _activate(self) -> None:
        if not self._bridge.is_available():
            self._set_status("tmux not found", "red")
            return

        sessions = self._bridge.discover_sessions()
        if not sessions:
            self._set_status("No cg/* sessions found", "yellow")
            return

        self._matcher.update_sessions(sessions)
        self._session_selector.set_sessions([s.name for s in sessions])

        # Create and start VAD recorder
        self._vad = VADRecorder(
            sample_rate=self._config.audio.sample_rate,
            channels=self._config.audio.channels,
            temp_dir=self._config.get_temp_dir(),
            threshold=self._config.hotmic.threshold,
            silence_duration=self._config.hotmic.silence_duration,
            min_segment=self._config.hotmic.min_segment,
        )
        self._vad.segment_ready.connect(self._on_segment_ready)
        self._vad.level_changed.connect(self._on_level_changed)

        # Use the same device the main window has selected
        device_index = self._get_device_index()
        try:
            self._vad.start_listening(device_index)
        except Exception as e:
            self._set_status(f"Mic error: {e}", "red")
            self._vad = None
            return

        self._is_active = True
        self._refresh_timer.start()
        self._update_toggle_style(True)
        self._set_panel_enabled(True)
        self._set_status("Listening...", "green")
        self.active_changed.emit(True)

    def _deactivate(self) -> None:
        self._refresh_timer.stop()
        self._accumulation_timer.stop()
        self._accumulated_text.clear()

        if self._vad is not None:
            self._vad.stop_listening()
            self._vad = None

        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(3000)
            self._worker = None

        self._is_active = False
        self._update_toggle_style(False)
        self._set_panel_enabled(False)
        self._set_status("Inactive", None)
        self._level_meter.reset()
        self.active_changed.emit(False)

    def _get_device_index(self) -> Optional[int]:
        """Get the device index from the parent main window's combo box."""
        main_window = self.window()
        if hasattr(main_window, "mic_combo"):
            device = main_window.mic_combo.currentData()
            if device is not None:
                return device.index
        return None

    def _set_panel_enabled(self, enabled: bool) -> None:
        """Enable/disable interactive panel elements."""
        self._session_selector.setEnabled(enabled)
        self._level_meter.setEnabled(enabled)

    def _update_toggle_style(self, active: bool) -> None:
        if active:
            self._toggle_btn.setText("ON")
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(80, 200, 100, 60);
                    color: #50c864;
                    border: 1px solid #50c864;
                    border-radius: 14px;
                    font-size: 11px;
                    font-weight: 700;
                    min-width: 0;
                }
                QPushButton:hover {
                    background-color: rgba(80, 200, 100, 80);
                }
            """)
        else:
            self._toggle_btn.setText("OFF")
            self._toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(100, 100, 110, 40);
                    color: #808088;
                    border: 1px solid #3a3a42;
                    border-radius: 14px;
                    font-size: 11px;
                    font-weight: 600;
                    min-width: 0;
                }
                QPushButton:hover {
                    background-color: rgba(100, 100, 110, 60);
                    color: #a0a0a8;
                }
            """)

    def _set_status(self, text: str, led_color: Optional[str] = None) -> None:
        self._status_label.setText(text)
        if led_color == "green":
            self._status_led.set_color(LEDIndicator.COLOR_GREEN)
            self._status_led.set_on(True)
        elif led_color == "red":
            self._status_led.set_color(LEDIndicator.COLOR_RED)
            self._status_led.set_on(True)
        elif led_color == "yellow":
            self._status_led.set_color(LEDIndicator.COLOR_YELLOW)
            self._status_led.set_on(True)
        elif led_color == "blue":
            self._status_led.set_color(LEDIndicator.COLOR_BLUE)
            self._status_led.set_on(True)
        else:
            self._status_led.set_on(False)

    @Slot()
    def _refresh_sessions(self) -> None:
        """Periodically refresh the session list."""
        sessions = self._bridge.discover_sessions()
        self._matcher.update_sessions(sessions)
        self._session_selector.set_sessions([s.name for s in sessions])

    @Slot(str)
    def _on_session_selected(self, name: str) -> None:
        """Handle manual session selection via pill click."""
        self._session_selector.set_active(name)

    @Slot(float)
    def _on_level_changed(self, level: float) -> None:
        if self._is_active:
            self._level_meter.set_level(level)

    @Slot(Path)
    def _on_segment_ready(self, audio_path: Path) -> None:
        """Handle a completed VAD speech segment."""
        if not self._is_active:
            return

        # Skip if already transcribing
        if self._worker is not None and self._worker.isRunning():
            # Clean up the segment file we can't process
            try:
                audio_path.unlink(missing_ok=True)
            except Exception:
                pass
            return

        self._set_status("Transcribing...", "blue")
        self._worker = _TranscribeWorker(self._transcriber, audio_path)
        self._worker.finished.connect(self._on_transcription_done)
        self._worker.error.connect(self._on_transcription_error)
        self._worker.start()

    @Slot(str)
    def _on_transcription_done(self, transcript: str) -> None:
        """Handle completed transcription — accumulate until stop word."""
        if not self._is_active:
            return

        stop_word = self._config.hotmic.stop_word.lower()
        submit_word = self._config.hotmic.submit_word.lower()

        words = transcript.strip().split()
        if not words:
            return

        # Normalize trailing words for comparison
        last_word = words[-1].rstrip(".,!?").lower()
        second_last = words[-2].rstrip(".,!?").lower() if len(words) >= 2 else ""

        # Check for "<stop_word> <submit_word>" → dispatch + Enter
        # Check for "<stop_word>" alone → dispatch (no Enter)
        press_enter = False
        if last_word == submit_word and second_last == stop_word:
            # Strip both stop word and submit word
            stripped = " ".join(words[:-2]).strip()
            press_enter = True
        elif last_word == stop_word:
            # Strip just the stop word
            stripped = " ".join(words[:-1]).strip()
        else:
            # No stop word — accumulate and continue listening
            self._accumulated_text.append(transcript.strip())
            preview = " ".join(self._accumulated_text) + " ..."
            self._preview.setPlainText(preview)
            self._set_status("Accumulating...", "blue")

            # Restart the accumulation timeout
            timeout_ms = int(self._config.hotmic.accumulation_timeout * 1000)
            self._accumulation_timer.start(timeout_ms)
            return

        # Stop word detected — dispatch accumulated buffer
        if stripped:
            self._accumulated_text.append(stripped)

        if self._accumulated_text:
            full_text = " ".join(self._accumulated_text)
            self._accumulated_text.clear()
            self._accumulation_timer.stop()
            self._dispatch_text(full_text, press_enter=press_enter)
        else:
            # Just the stop word with empty buffer — clear/cancel
            self._accumulated_text.clear()
            self._accumulation_timer.stop()
            self._preview.setPlainText("[buffer cleared]")
            self._set_status("Buffer cleared", "yellow")

    def _dispatch_text(self, text: str, press_enter: bool = False) -> None:
        """Match session name in text and dispatch command to tmux."""
        self._preview.setPlainText(text)

        result = self._matcher.match(text)
        if result is not None:
            self._session_selector.set_active(result.session.name)

            if result.command_text:
                success = self._bridge.send_text(
                    result.session.name, result.command_text
                )
                if success and press_enter:
                    self._bridge.send_enter(result.session.name)

                suffix = " + Enter" if press_enter else ""
                if success:
                    self._set_status(
                        f"Sent to {result.session.name}{suffix}", "green"
                    )
                else:
                    self._set_status(
                        f"Failed to send to {result.session.name}", "red"
                    )
            else:
                self._set_status(
                    f"Matched {result.session.name} (no command)", "yellow"
                )
        else:
            self._set_status("No session match", "yellow")

    @Slot()
    def _on_accumulation_timeout(self) -> None:
        """Discard buffer after prolonged silence."""
        self._accumulated_text.clear()
        self._preview.setPlainText("[buffer timed out]")
        self._set_status("Buffer timed out", "yellow")

    @Slot(str)
    def _on_transcription_error(self, error_msg: str) -> None:
        if self._is_active:
            self._set_status(f"Error: {error_msg}", "red")
