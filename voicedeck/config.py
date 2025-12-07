"""Configuration management for VoiceDeck."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import toml


@dataclass
class STTConfig:
    """Speech-to-text backend configuration."""
    provider: str = "openai"
    model: str = "whisper-1"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    max_chunk_seconds: int = 600  # 10 minutes per chunk
    max_chunk_mb: int = 24  # OpenAI limit is 25MB, use 24 for safety


@dataclass
class AudioConfig:
    """Audio recording configuration."""
    sample_rate: int = 16000
    channels: int = 1
    temp_dir: Optional[str] = None


@dataclass
class ShortcutsConfig:
    """Keyboard shortcuts configuration."""
    toggle_recording: str = "Ctrl+Space"
    copy_transcript: str = "Ctrl+Shift+C"


@dataclass
class AppConfig:
    """Application configuration."""
    stt: STTConfig = field(default_factory=STTConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    shortcuts: ShortcutsConfig = field(default_factory=ShortcutsConfig)
    cleanup_audio_after_transcription: bool = True

    @classmethod
    def get_config_path(cls) -> Path:
        """Return the primary config file path."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(xdg_config) / "voicedeck" / "config.toml"

    @classmethod
    def get_config_paths(cls) -> list[Path]:
        """Return list of config file paths to check, in priority order."""
        paths = []

        # XDG config directory (primary)
        paths.append(cls.get_config_path())

        # Home directory
        paths.append(Path.home() / ".voicedeck.toml")

        # Current working directory (for development)
        paths.append(Path.cwd() / "config.toml")

        return paths

    @classmethod
    def load(cls) -> "AppConfig":
        """Load configuration from file and environment variables."""
        config = cls()

        # Try loading from config files
        for config_path in cls.get_config_paths():
            if config_path.exists():
                try:
                    data = toml.load(config_path)
                    config = cls._from_dict(data)
                    break
                except Exception:
                    # Invalid config file, continue to next
                    continue

        # Environment variables override config file
        if api_key := os.environ.get("OPENAI_API_KEY"):
            config.stt.api_key = api_key

        if base_url := os.environ.get("OPENAI_BASE_URL"):
            config.stt.base_url = base_url

        if model := os.environ.get("VOICEDECK_STT_MODEL"):
            config.stt.model = model

        if provider := os.environ.get("VOICEDECK_STT_PROVIDER"):
            config.stt.provider = provider

        return config

    @classmethod
    def _from_dict(cls, data: dict) -> "AppConfig":
        """Create config from dictionary."""
        config = cls()

        if "stt" in data:
            stt_data = data["stt"]
            config.stt.provider = stt_data.get("provider", config.stt.provider)
            config.stt.model = stt_data.get("model", config.stt.model)
            config.stt.base_url = stt_data.get("base_url", config.stt.base_url)
            config.stt.api_key = stt_data.get("api_key", config.stt.api_key)
            config.stt.max_chunk_seconds = stt_data.get(
                "max_chunk_seconds", config.stt.max_chunk_seconds
            )
            config.stt.max_chunk_mb = stt_data.get(
                "max_chunk_mb", config.stt.max_chunk_mb
            )

        if "audio" in data:
            audio_data = data["audio"]
            config.audio.sample_rate = audio_data.get(
                "sample_rate", config.audio.sample_rate
            )
            config.audio.channels = audio_data.get("channels", config.audio.channels)
            config.audio.temp_dir = audio_data.get("temp_dir", config.audio.temp_dir)

        if "shortcuts" in data:
            shortcuts_data = data["shortcuts"]
            config.shortcuts.toggle_recording = shortcuts_data.get(
                "toggle_recording", config.shortcuts.toggle_recording
            )
            config.shortcuts.copy_transcript = shortcuts_data.get(
                "copy_transcript", config.shortcuts.copy_transcript
            )

        config.cleanup_audio_after_transcription = data.get(
            "cleanup_audio_after_transcription",
            config.cleanup_audio_after_transcription
        )

        return config

    def to_dict(self) -> dict:
        """Convert config to dictionary for saving."""
        data = {
            "stt": {
                "provider": self.stt.provider,
                "model": self.stt.model,
                "max_chunk_seconds": self.stt.max_chunk_seconds,
                "max_chunk_mb": self.stt.max_chunk_mb,
            },
            "audio": {
                "sample_rate": self.audio.sample_rate,
                "channels": self.audio.channels,
            },
            "shortcuts": {
                "toggle_recording": self.shortcuts.toggle_recording,
                "copy_transcript": self.shortcuts.copy_transcript,
            },
            "cleanup_audio_after_transcription": self.cleanup_audio_after_transcription,
        }

        # Only include optional fields if set
        if self.stt.base_url:
            data["stt"]["base_url"] = self.stt.base_url
        if self.stt.api_key:
            data["stt"]["api_key"] = self.stt.api_key
        if self.audio.temp_dir:
            data["audio"]["temp_dir"] = self.audio.temp_dir

        return data

    def get_temp_dir(self) -> Path:
        """Get the temporary directory for audio files."""
        if self.audio.temp_dir:
            temp_path = Path(self.audio.temp_dir)
        else:
            xdg_cache = os.environ.get(
                "XDG_CACHE_HOME", os.path.expanduser("~/.cache")
            )
            temp_path = Path(xdg_cache) / "voicedeck"

        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path


def save_config(config: AppConfig) -> None:
    """Save configuration to the primary config file."""
    config_path = AppConfig.get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        toml.dump(config.to_dict(), f)
