"""Main application window for VoiceDeck."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, Slot
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
)

from ..audio import AudioRecorder, AudioDevice, RecorderError
from ..stt import Transcriber, TranscriberError
from ..config import AppConfig
from .styles import DARK_STYLESHEET


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

        self._setup_ui()
        self._setup_shortcuts()
        self._refresh_devices()
        self._update_ui_state()

    def _setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("VoiceDeck")
        self.setMinimumSize(500, 450)
        self.resize(550, 500)
        self.setStyleSheet(DARK_STYLESHEET)

        # Central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Microphone selector
        mic_layout = QHBoxLayout()
        mic_label = QLabel("Microphone:")
        mic_label.setFixedWidth(90)
        self.mic_combo = QComboBox()
        self.mic_combo.setMinimumWidth(300)
        mic_layout.addWidget(mic_label)
        mic_layout.addWidget(self.mic_combo, 1)
        layout.addLayout(mic_layout)

        # Record button
        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setObjectName("recordButton")
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # Transcript area
        transcript_label = QLabel("Transcript:")
        layout.addWidget(transcript_label)

        self.transcript_edit = QTextEdit()
        self.transcript_edit.setReadOnly(True)
        self.transcript_edit.setPlaceholderText(
            "Your transcribed text will appear here..."
        )
        self.transcript_edit.setMinimumHeight(150)
        layout.addWidget(self.transcript_edit, 1)

        # Button row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

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
        """Set up keyboard shortcuts."""
        # Ctrl+Space to toggle recording
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+Space"), self)
        toggle_shortcut.activated.connect(self._toggle_recording)

        # Ctrl+C when transcript is focused copies all (handled by QTextEdit)
        # Ctrl+Shift+C to copy transcript from anywhere
        copy_shortcut = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        copy_shortcut.activated.connect(self._copy_transcript)

    def _refresh_devices(self):
        """Refresh the list of available audio devices."""
        self.mic_combo.clear()
        self._devices = []

        try:
            self._devices = AudioRecorder.list_devices()
        except RecorderError as e:
            self._set_status(f"Error: {e}", error=True)
            return

        if not self._devices:
            self.mic_combo.addItem("No microphones found")
            self.mic_combo.setEnabled(False)
            self.record_btn.setEnabled(False)
            return

        self.mic_combo.setEnabled(True)
        self.record_btn.setEnabled(True)

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
        self, text: str, recording: bool = False, transcribing: bool = False, error: bool = False
    ):
        """Update the status label."""
        if error:
            self.status_label.setText(f"Error: {text}")
        else:
            self.status_label.setText(text)

        self.status_label.setProperty("recording", recording)
        self.status_label.setProperty("transcribing", transcribing)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _update_ui_state(self):
        """Update UI element states based on current recording state."""
        is_recording = self.recorder.is_recording
        is_transcribing = (
            self._transcription_worker is not None
            and self._transcription_worker.isRunning()
        )

        # Update record button
        self.record_btn.setProperty("recording", is_recording)
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)

        if is_recording:
            self.record_btn.setText("Stop Recording")
            self.record_btn.setEnabled(True)
        elif is_transcribing:
            self.record_btn.setText("Start Recording")
            self.record_btn.setEnabled(False)
        else:
            self.record_btn.setText("Start Recording")
            self.record_btn.setEnabled(bool(self._devices))

        # Disable mic selection during recording or transcription
        self.mic_combo.setEnabled(not is_recording and not is_transcribing and bool(self._devices))

        # Enable copy/clear only when there's transcript text
        has_transcript = bool(self.transcript_edit.toPlainText().strip())
        self.copy_btn.setEnabled(has_transcript)
        self.clear_btn.setEnabled(has_transcript or is_recording or is_transcribing)

    @Slot()
    def _toggle_recording(self):
        """Toggle recording on/off."""
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        """Start a new recording session."""
        device = self._get_selected_device()
        if device is None:
            self._set_status("No microphone selected", error=True)
            return

        # Check if transcriber is configured
        if not self.transcriber.is_configured():
            error_msg = self.transcriber.get_configuration_error()
            QMessageBox.warning(
                self,
                "Configuration Required",
                error_msg or "STT backend is not configured.",
            )
            return

        try:
            self._current_audio_path = self.recorder.start(device)
            self._set_status("Recording...", recording=True)
            self._update_ui_state()
        except RecorderError as e:
            self._set_status(str(e), error=True)

    def _stop_recording(self):
        """Stop recording and start transcription."""
        audio_path = self.recorder.stop()
        self._update_ui_state()

        if audio_path is None or not audio_path.exists():
            self._set_status("Recording failed - no audio file", error=True)
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

    @Slot(str)
    def _on_transcription_complete(self, transcript: str):
        """Handle successful transcription."""
        self.transcript_edit.setPlainText(transcript)
        self._set_status("Ready")
        self._cleanup_audio()
        self._update_ui_state()

    @Slot(str)
    def _on_transcription_error(self, error_msg: str):
        """Handle transcription error."""
        self._set_status(error_msg, error=True)
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
            self._set_status("Copied to clipboard")

    @Slot()
    def _clear_transcript(self):
        """Clear the transcript and reset to ready state."""
        # Stop any ongoing recording
        if self.recorder.is_recording:
            self.recorder.stop()

        self.transcript_edit.clear()
        self._current_audio_path = None
        self._set_status("Ready")
        self._update_ui_state()

    def closeEvent(self, event):
        """Handle window close event."""
        # Stop recording if active
        if self.recorder.is_recording:
            self.recorder.stop()

        # Wait for transcription to complete
        if self._transcription_worker and self._transcription_worker.isRunning():
            self._transcription_worker.wait(5000)  # Wait up to 5 seconds

        event.accept()
