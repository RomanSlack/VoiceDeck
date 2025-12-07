"""Base interface for speech-to-text backends."""

from abc import ABC, abstractmethod
from pathlib import Path


class TranscriberError(Exception):
    """Exception raised for transcription errors."""
    pass


class Transcriber(ABC):
    """Abstract base class for speech-to-text transcribers."""

    @abstractmethod
    def transcribe(self, file_path: Path) -> str:
        """
        Transcribe an audio file to text.

        Args:
            file_path: Path to the audio file (WAV, FLAC, MP3, etc.)

        Returns:
            The transcribed text.

        Raises:
            TranscriberError: If transcription fails.
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the transcriber is properly configured.

        Returns:
            True if ready to transcribe, False otherwise.
        """
        pass

    @abstractmethod
    def get_configuration_error(self) -> str | None:
        """
        Get a human-readable error message if not configured.

        Returns:
            Error message or None if properly configured.
        """
        pass
