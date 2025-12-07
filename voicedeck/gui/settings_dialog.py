"""Settings dialog for VoiceDeck."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QTabWidget,
    QWidget,
    QFormLayout,
    QMessageBox,
    QKeySequenceEdit,
    QCheckBox,
    QSpinBox,
    QGroupBox,
)

from ..config import AppConfig, save_config
from ..keyring_storage import get_api_key, set_api_key, delete_api_key, is_keyring_available


class SettingsDialog(QDialog):
    """Settings dialog with tabs for API, audio, and shortcuts."""

    settings_changed = Signal()

    def __init__(self, config: AppConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Initialize the settings UI."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # API Settings tab
        self._create_api_tab()

        # Audio Settings tab
        self._create_audio_tab()

        # Shortcuts tab
        self._create_shortcuts_tab()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setDefault(True)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _create_api_tab(self):
        """Create the API settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # OpenAI API Group
        api_group = QGroupBox("OpenAI API")
        api_layout = QFormLayout(api_group)

        # API Key
        key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("sk-...")
        key_layout.addWidget(self.api_key_edit)

        self.show_key_btn = QPushButton("Show")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.toggled.connect(self._toggle_key_visibility)
        self.show_key_btn.setFixedWidth(60)
        key_layout.addWidget(self.show_key_btn)

        api_layout.addRow("API Key:", key_layout)

        # Keyring status
        if is_keyring_available():
            keyring_label = QLabel("API key will be stored securely in system keyring")
            keyring_label.setStyleSheet("color: #4ecdc4; font-size: 12px;")
        else:
            keyring_label = QLabel("System keyring unavailable - key stored in config file")
            keyring_label.setStyleSheet("color: #ffaa00; font-size: 12px;")
        api_layout.addRow("", keyring_label)

        # Base URL (optional)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1 (default)")
        api_layout.addRow("Base URL:", self.base_url_edit)

        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.addItems([
            "whisper-1",
            "gpt-4o-transcribe",
            "gpt-4o-mini-transcribe",
        ])
        api_layout.addRow("Model:", self.model_combo)

        layout.addWidget(api_group)

        # Chunking settings
        chunk_group = QGroupBox("Long Recording Settings")
        chunk_layout = QFormLayout(chunk_group)

        self.chunk_seconds_spin = QSpinBox()
        self.chunk_seconds_spin.setRange(60, 3600)
        self.chunk_seconds_spin.setSuffix(" seconds")
        self.chunk_seconds_spin.setSingleStep(60)
        chunk_layout.addRow("Max chunk duration:", self.chunk_seconds_spin)

        self.chunk_mb_spin = QSpinBox()
        self.chunk_mb_spin.setRange(1, 24)
        self.chunk_mb_spin.setSuffix(" MB")
        chunk_layout.addRow("Max chunk size:", self.chunk_mb_spin)

        layout.addWidget(chunk_group)
        layout.addStretch()

        self.tabs.addTab(tab, "API")

    def _create_audio_tab(self):
        """Create the audio settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        audio_group = QGroupBox("Recording Settings")
        audio_layout = QFormLayout(audio_group)

        # Sample rate
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["16000", "22050", "44100", "48000"])
        audio_layout.addRow("Sample Rate (Hz):", self.sample_rate_combo)

        # Channels
        self.channels_combo = QComboBox()
        self.channels_combo.addItems(["1 (Mono)", "2 (Stereo)"])
        audio_layout.addRow("Channels:", self.channels_combo)

        # Cleanup
        self.cleanup_check = QCheckBox("Delete audio files after transcription")
        audio_layout.addRow("", self.cleanup_check)

        layout.addWidget(audio_group)
        layout.addStretch()

        self.tabs.addTab(tab, "Audio")

    def _create_shortcuts_tab(self):
        """Create the keyboard shortcuts tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QFormLayout(shortcuts_group)

        # Record toggle shortcut
        self.record_shortcut_edit = QKeySequenceEdit()
        self.record_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Space"))
        shortcuts_layout.addRow("Toggle Recording:", self.record_shortcut_edit)

        # Copy shortcut
        self.copy_shortcut_edit = QKeySequenceEdit()
        self.copy_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Shift+C"))
        shortcuts_layout.addRow("Copy Transcript:", self.copy_shortcut_edit)

        # Reset button
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_shortcuts)
        shortcuts_layout.addRow("", reset_btn)

        layout.addWidget(shortcuts_group)

        # Info label
        info_label = QLabel(
            "Note: Shortcuts only work when the application window is focused."
        )
        info_label.setStyleSheet("color: #808080; font-size: 12px;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()

        self.tabs.addTab(tab, "Shortcuts")

    def _toggle_key_visibility(self, show: bool):
        """Toggle API key visibility."""
        if show:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_key_btn.setText("Hide")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_key_btn.setText("Show")

    def _reset_shortcuts(self):
        """Reset shortcuts to defaults."""
        self.record_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Space"))
        self.copy_shortcut_edit.setKeySequence(QKeySequence("Ctrl+Shift+C"))

    def _load_settings(self):
        """Load current settings into the UI."""
        # API settings
        api_key = get_api_key() or self.config.stt.api_key or ""
        self.api_key_edit.setText(api_key)
        self.base_url_edit.setText(self.config.stt.base_url or "")

        # Find and set model in combo
        model = self.config.stt.model
        idx = self.model_combo.findText(model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setCurrentText(model)

        self.chunk_seconds_spin.setValue(self.config.stt.max_chunk_seconds)
        self.chunk_mb_spin.setValue(self.config.stt.max_chunk_mb)

        # Audio settings
        sample_rate_idx = self.sample_rate_combo.findText(str(self.config.audio.sample_rate))
        if sample_rate_idx >= 0:
            self.sample_rate_combo.setCurrentIndex(sample_rate_idx)

        self.channels_combo.setCurrentIndex(self.config.audio.channels - 1)
        self.cleanup_check.setChecked(self.config.cleanup_audio_after_transcription)

        # Shortcuts
        self.record_shortcut_edit.setKeySequence(
            QKeySequence(self.config.shortcuts.toggle_recording)
        )
        self.copy_shortcut_edit.setKeySequence(
            QKeySequence(self.config.shortcuts.copy_transcript)
        )

    def _save_settings(self):
        """Save settings and close dialog."""
        # Validate API key
        api_key = self.api_key_edit.text().strip()
        if api_key and not api_key.startswith("sk-"):
            QMessageBox.warning(
                self,
                "Invalid API Key",
                "OpenAI API keys should start with 'sk-'.\n"
                "Please check your API key and try again.",
            )
            return

        # Save API key to keyring (or config as fallback)
        if api_key:
            if is_keyring_available():
                set_api_key(api_key)
                self.config.stt.api_key = None  # Don't store in config file
            else:
                self.config.stt.api_key = api_key
        else:
            if is_keyring_available():
                delete_api_key()
            self.config.stt.api_key = None

        # Save other API settings
        base_url = self.base_url_edit.text().strip()
        self.config.stt.base_url = base_url if base_url else None
        self.config.stt.model = self.model_combo.currentText()
        self.config.stt.max_chunk_seconds = self.chunk_seconds_spin.value()
        self.config.stt.max_chunk_mb = self.chunk_mb_spin.value()

        # Save audio settings
        self.config.audio.sample_rate = int(self.sample_rate_combo.currentText())
        self.config.audio.channels = self.channels_combo.currentIndex() + 1
        self.config.cleanup_audio_after_transcription = self.cleanup_check.isChecked()

        # Save shortcuts
        self.config.shortcuts.toggle_recording = self.record_shortcut_edit.keySequence().toString()
        self.config.shortcuts.copy_transcript = self.copy_shortcut_edit.keySequence().toString()

        # Write config to file
        save_config(self.config)

        self.settings_changed.emit()
        self.accept()
