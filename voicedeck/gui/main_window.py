"""Main application window for VoiceDeck."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QTextEdit,
    QApplication,
    QMessageBox,
    QFrame,
)

from ..audio import AudioRecorder, AudioDevice, RecorderError
from ..stt import Transcriber, TranscriberError
from ..stt.openai_client import create_transcriber
from ..config import AppConfig
from ..keyring_storage import get_api_key
from .styles import DARK_STYLESHEET
from .settings_dialog import SettingsDialog
from .widgets import RecordButton, LevelMeter, LEDIndicator


class TranscriptionWorker(QThread):
    """Background worker for audio transcription."""

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


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: AppConfig, transcriber: Transcriber):
        super().__init__()

        self.config = config
        self.transcriber = transcriber
        self.recorder = AudioRecorder(
            sample_rate=config.audio.sample_rate,
            channels=config.audio.channels,
            temp_dir=config.get_temp_dir(),
        )

        self._current_audio_path: Optional[Path] = None
        self._transcription_worker: Optional[TranscriptionWorker] = None
        self._devices: list[AudioDevice] = []
        self._shortcuts: list[QShortcut] = []

        # Level meter update timer
        self._level_timer = QTimer(self)
        self._level_timer.timeout.connect(self._update_level_meter)
        self._level_timer.setInterval(50)  # 20 FPS

        self._setup_ui()
        self._setup_shortcuts()
        self._refresh_devices()
        self._update_ui_state()
        self._check_api_key_on_start()

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("VoiceDeck")
        self.setMinimumSize(520, 540)
        self.resize(560, 580)
        self.setStyleSheet(DARK_STYLESHEET)

        # Central widget and layout
        central = QWidget()
        central.setObjectName("centralWidget")
        central.setAutoFillBackground(True)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        # Top bar with settings button
        top_bar = QHBoxLayout()

        # App title
        title_label = QLabel("VoiceDeck")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: 600;
            color: #c0c0c8;
            letter-spacing: 1px;
        """)
        top_bar.addWidget(title_label)
        top_bar.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.clicked.connect(self._open_settings)
        top_bar.addWidget(self.settings_btn)

        layout.addLayout(top_bar)

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2a2a32; max-height: 1px;")
        layout.addWidget(separator)

        # Microphone section
        mic_section = QLabel("INPUT DEVICE")
        mic_section.setObjectName("sectionLabel")
        layout.addWidget(mic_section)

        mic_layout = QHBoxLayout()
        mic_layout.setSpacing(12)

        # LED indicator for mic status
        self.mic_led = LEDIndicator(color=LEDIndicator.COLOR_GREEN)
        mic_layout.addWidget(self.mic_led)

        self.mic_combo = QComboBox()
        self.mic_combo.setMinimumWidth(320)
        mic_layout.addWidget(self.mic_combo, 1)
        layout.addLayout(mic_layout)

        # Level meter
        self.level_meter = LevelMeter()
        layout.addWidget(self.level_meter)

        layout.addSpacing(8)

        # Record button (custom widget)
        self.record_btn = RecordButton()
        self.record_btn.recordingToggled.connect(self._on_record_toggled)
        self.record_btn.setEnabled(False)
        layout.addWidget(self.record_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status section
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        self.status_led = LEDIndicator()
        status_layout.addWidget(self.status_led)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label, 1)

        layout.addLayout(status_layout)

        layout.addSpacing(4)

        # Transcript section
        transcript_label = QLabel("TRANSCRIPT")
        transcript_label.setObjectName("sectionLabel")
        layout.addWidget(transcript_label)

        self.transcript_edit = QTextEdit()
        self.transcript_edit.setReadOnly(True)
        self.transcript_edit.setPlaceholderText(
            "Your transcribed text will appear here..."
        )
        self.transcript_edit.setMinimumHeight(160)
        layout.addWidget(self.transcript_edit, 1)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copyButton")
        self.copy_btn.clicked.connect(self._copy_transcript)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self._clear_transcript)

        btn_layout.addStretch()
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

    def _setup_shortcuts(self):
        """Set up keyboard shortcuts from config."""
        # Clear existing shortcuts
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self._shortcuts.clear()

        # Toggle recording shortcut
        toggle_shortcut = QShortcut(
            QKeySequence(self.config.shortcuts.toggle_recording), self
        )
        toggle_shortcut.activated.connect(self._toggle_recording)
        self._shortcuts.append(toggle_shortcut)

        # Copy transcript shortcut
        copy_shortcut = QShortcut(
            QKeySequence(self.config.shortcuts.copy_transcript), self
        )
        copy_shortcut.activated.connect(self._copy_transcript)
        self._shortcuts.append(copy_shortcut)

    def _check_api_key_on_start(self):
        """Check if API key is configured on startup."""
        # Check keyring first, then config, then env
        api_key = get_api_key() or self.config.stt.api_key
        if not api_key:
            # Show a friendly prompt to configure
            QMessageBox.information(
                self,
                "Welcome to VoiceDeck",
                "To get started, please configure your OpenAI API key.\n\n"
                "Click Settings to enter your API key.",
            )

    def _open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self.config, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    @Slot()
    def _on_settings_changed(self):
        """Handle settings changes."""
        # Reload config
        self.config = AppConfig.load()

        # Update API key from keyring
        api_key = get_api_key()
        if api_key:
            self.config.stt.api_key = api_key

        # Recreate transcriber with new settings
        try:
            self.transcriber = create_transcriber(self.config.stt)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Configuration Error",
                f"Failed to apply settings: {e}",
            )
            return

        # Recreate recorder with new audio settings
        self.recorder = AudioRecorder(
            sample_rate=self.config.audio.sample_rate,
            channels=self.config.audio.channels,
            temp_dir=self.config.get_temp_dir(),
        )

        # Update shortcuts
        self._setup_shortcuts()

        self._set_status("Settings saved", "green")

    def _refresh_devices(self):
        """Refresh the list of available audio devices."""
        self.mic_combo.clear()
        self._devices = []

        try:
            self._devices = AudioRecorder.list_devices()
        except RecorderError as e:
            self._set_status(f"Error: {e}", "red")
            return

        if not self._devices:
            self.mic_combo.addItem("No microphones found")
            self.mic_combo.setEnabled(False)
            self.record_btn.setEnabled(False)
            self.mic_led.set_color(LEDIndicator.COLOR_RED)
            self.mic_led.set_on(True)
            return

        self.mic_combo.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.mic_led.set_color(LEDIndicator.COLOR_GREEN)
        self.mic_led.set_on(True)

        # Add devices to combo box
        default_device = AudioRecorder.get_default_device()
        default_index = 0

        for i, device in enumerate(self._devices):
            self.mic_combo.addItem(device.name, device)
            if default_device and device.index == default_device.index:
                default_index = i

        self.mic_combo.setCurrentIndex(default_index)

    def _get_selected_device(self) -> Optional[AudioDevice]:
        """Get the currently selected audio device."""
        return self.mic_combo.currentData()

    def _set_status(
        self, text: str, led_color: str = None, recording: bool = False, transcribing: bool = False
    ):
        """Update the status label and LED."""
        self.status_label.setText(text)
        self.status_label.setProperty("recording", recording)
        self.status_label.setProperty("transcribing", transcribing)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

        # Update status LED
        if led_color == "red":
            self.status_led.set_color(LEDIndicator.COLOR_RED)
            self.status_led.set_on(True)
        elif led_color == "green":
            self.status_led.set_color(LEDIndicator.COLOR_GREEN)
            self.status_led.set_on(True)
        elif led_color == "yellow":
            self.status_led.set_color(LEDIndicator.COLOR_YELLOW)
            self.status_led.set_on(True)
        elif led_color == "blue":
            self.status_led.set_color(LEDIndicator.COLOR_BLUE)
            self.status_led.set_on(True)
        elif recording:
            self.status_led.set_color(LEDIndicator.COLOR_RED)
            self.status_led.set_on(True)
        elif transcribing:
            self.status_led.set_color(LEDIndicator.COLOR_BLUE)
            self.status_led.set_on(True)
        else:
            self.status_led.set_on(False)

    def _update_ui_state(self):
        """Update UI element states based on current recording state."""
        is_recording = self.recorder.is_recording
        is_transcribing = (
            self._transcription_worker is not None
            and self._transcription_worker.isRunning()
        )

        # Update record button state (it handles its own appearance)
        self.record_btn.set_recording(is_recording)

        if is_recording:
            self.record_btn.setEnabled(True)
        elif is_transcribing:
            self.record_btn.setEnabled(False)
        else:
            self.record_btn.setEnabled(bool(self._devices))

        # Disable mic selection during recording or transcription
        self.mic_combo.setEnabled(not is_recording and not is_transcribing and bool(self._devices))

        # Enable copy/clear only when there's transcript text
        has_transcript = bool(self.transcript_edit.toPlainText().strip())
        self.copy_btn.setEnabled(has_transcript)
        self.clear_btn.setEnabled(has_transcript or is_recording or is_transcribing)

        # Disable settings during recording/transcription
        self.settings_btn.setEnabled(not is_recording and not is_transcribing)

    @Slot(bool)
    def _on_record_toggled(self, recording: bool):
        """Handle record button toggle (from custom widget click)."""
        # The button already toggled its visual state, so we just need to
        # start/stop recording. If something fails, we'll reset the button.
        if recording:
            success = self._start_recording()
            if not success:
                self.record_btn.set_recording(False)
        else:
            self._stop_recording()

    @Slot()
    def _toggle_recording(self):
        """Toggle recording on/off (from keyboard shortcut)."""
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> bool:
        """Start a new recording session. Returns True on success."""
        device = self._get_selected_device()
        if device is None:
            self._set_status("No microphone selected", "red")
            return False

        # Check if transcriber is configured (check keyring too)
        api_key = get_api_key() or self.config.stt.api_key
        if not api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please configure your OpenAI API key in Settings.",
            )
            self._open_settings()
            return False

        # Update transcriber with keyring API key if needed
        if api_key and not self.transcriber.is_configured():
            self.config.stt.api_key = api_key
            try:
                self.transcriber = create_transcriber(self.config.stt)
            except Exception as e:
                self._set_status(str(e), "red")
                return False

        try:
            self._current_audio_path = self.recorder.start(device)
            self._set_status("Recording...", recording=True)
            self.record_btn.set_recording(True)
            self._level_timer.start()
            self._update_ui_state()
            return True
        except RecorderError as e:
            self._set_status(str(e), "red")
            return False

    def _stop_recording(self):
        """Stop recording and start transcription."""
        self._level_timer.stop()
        self.level_meter.reset()

        audio_path = self.recorder.stop()
        self.record_btn.set_recording(False)
        self._update_ui_state()

        if audio_path is None or not audio_path.exists():
            self._set_status("Recording failed - no audio file", "red")
            return

        self._current_audio_path = audio_path
        self._start_transcription(audio_path)

    def _start_transcription(self, audio_path: Path):
        """Start background transcription of the audio file."""
        self._set_status("Transcribing...", transcribing=True)
        self._update_ui_state()

        self._transcription_worker = TranscriptionWorker(self.transcriber, audio_path)
        self._transcription_worker.finished.connect(self._on_transcription_complete)
        self._transcription_worker.error.connect(self._on_transcription_error)
        self._transcription_worker.start()

    @Slot()
    def _update_level_meter(self):
        """Update the level meter with current audio level."""
        if self.recorder.is_recording:
            level = self.recorder.get_current_level()
            self.level_meter.set_level(level)

    @Slot(str)
    def _on_transcription_complete(self, transcript: str):
        """Handle successful transcription."""
        self.transcript_edit.setPlainText(transcript)
        self._set_status("Ready", "green")
        self._cleanup_audio()
        self._update_ui_state()

    @Slot(str)
    def _on_transcription_error(self, error_msg: str):
        """Handle transcription error."""
        self._set_status(f"Error: {error_msg}", "red")
        self._update_ui_state()

    def _cleanup_audio(self):
        """Clean up temporary audio file if configured."""
        if (
            self.config.cleanup_audio_after_transcription
            and self._current_audio_path
            and self._current_audio_path.exists()
        ):
            try:
                self._current_audio_path.unlink()
            except Exception:
                pass
        self._current_audio_path = None

    @Slot()
    def _copy_transcript(self):
        """Copy transcript to clipboard."""
        text = self.transcript_edit.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self._set_status("Copied to clipboard", "green")

    @Slot()
    def _clear_transcript(self):
        """Clear the transcript and reset to ready state."""
        # Stop any ongoing recording
        if self.recorder.is_recording:
            self._level_timer.stop()
            self.level_meter.reset()
            self.recorder.stop()
            self.record_btn.set_recording(False)

        self.transcript_edit.clear()
        self._current_audio_path = None
        self._set_status("Ready")
        self._update_ui_state()

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop level timer
        self._level_timer.stop()

        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop()

        # Wait for transcription to complete
        if self._transcription_worker and self._transcription_worker.isRunning():
            self._transcription_worker.wait(5000)  # Wait up to 5 seconds

        event.accept()
