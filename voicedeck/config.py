"""Configuration management for VoiceDeck."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import platformdirs
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
class HotMicConfig:
    """Hot mic mode configuration."""
    threshold: float = 0.02
    silence_duration: float = 1.5
    min_segment: float = 0.5
    match_confidence: float = 0.8
    stop_word: str = "moscow"
    submit_word: str = "delta"
    accumulation_timeout: float = 300.0


@dataclass
class ShortcutsConfig:
    """Keyboard shortcuts configuration."""
    toggle_recording: str = "Ctrl+Space"
    copy_transcript: str = "Ctrl+Shift+C"
    toggle_hotmic: str = "Ctrl+Shift+H"


@dataclass
class AppConfig:
    """Application configuration."""
    stt: STTConfig = field(default_factory=STTConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    shortcuts: ShortcutsConfig = field(default_factory=ShortcutsConfig)
    hotmic: HotMicConfig = field(default_factory=HotMicConfig)
    cleanup_audio_after_transcription: bool = True

    @classmethod
    def get_config_path(cls) -> Path:
        """Return the primary config file path."""
        config_dir = platformdirs.user_config_dir("VoiceDeck")
        return Path(config_dir) / "config.toml"

    @classmethod
    def get_config_paths(cls) -> list[Path]:
        """Return list of config file paths to check, in priority order."""
        paths = []

        # Platform config directory (primary)
        paths.append(cls.get_config_path())

        # Home directory
        paths.append(Path.home() / ".voicedeck.toml")

        # Current working directory (for development)
        paths.append(Path.cwd() / "config.toml")

        # Legacy Linux XDG path for existing users
        if sys.platform == "linux":
            xdg_config = os.environ.get(
                "XDG_CONFIG_HOME", os.path.expanduser("~/.config")
            )
            legacy_path = Path(xdg_config) / "voicedeck" / "config.toml"
            if legacy_path not in paths:
                paths.append(legacy_path)

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
            config.shortcuts.toggle_hotmic = shortcuts_data.get(
                "toggle_hotmic", config.shortcuts.toggle_hotmic
            )

        if "hotmic" in data:
            hm = data["hotmic"]
            config.hotmic.threshold = hm.get("threshold", config.hotmic.threshold)
            config.hotmic.silence_duration = hm.get(
                "silence_duration", config.hotmic.silence_duration
            )
            config.hotmic.min_segment = hm.get(
                "min_segment", config.hotmic.min_segment
            )
            config.hotmic.match_confidence = hm.get(
                "match_confidence", config.hotmic.match_confidence
            )
            config.hotmic.stop_word = hm.get(
                "stop_word", config.hotmic.stop_word
            )
            config.hotmic.submit_word = hm.get(
                "submit_word", config.hotmic.submit_word
            )
            config.hotmic.accumulation_timeout = hm.get(
                "accumulation_timeout", config.hotmic.accumulation_timeout
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
                "toggle_hotmic": self.shortcuts.toggle_hotmic,
            },
            "hotmic": {
                "threshold": self.hotmic.threshold,
                "silence_duration": self.hotmic.silence_duration,
                "min_segment": self.hotmic.min_segment,
                "match_confidence": self.hotmic.match_confidence,
                "stop_word": self.hotmic.stop_word,
                "submit_word": self.hotmic.submit_word,
                "accumulation_timeout": self.hotmic.accumulation_timeout,
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
            temp_path = Path(platformdirs.user_cache_dir("VoiceDeck"))

        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path


def save_config(config: AppConfig) -> None:
    """Save configuration to the primary config file."""
    config_path = AppConfig.get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w") as f:
        toml.dump(config.to_dict(), f)
