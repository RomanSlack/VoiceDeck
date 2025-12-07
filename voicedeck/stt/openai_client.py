"""OpenAI Speech-to-Text backend implementation."""

import os
import tempfile
import wave
from pathlib import Path
from typing import Optional

import numpy as np
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from scipy.io import wavfile

from .base import Transcriber, TranscriberError
from ..config import STTConfig


class OpenAITranscriber(Transcriber):
    """
    Transcriber implementation using OpenAI's Audio API.

    Handles long recordings by chunking audio files to stay within API limits.
    """

    def __init__(self, config: STTConfig):
        self.config = config
        self._client: Optional[OpenAI] = None

    def _get_client(self) -> OpenAI:
        """Get or create the OpenAI client."""
        if self._client is None:
            api_key = self.config.api_key
            if not api_key:
                raise TranscriberError(
                    "OpenAI API key not configured. "
                    "Set OPENAI_API_KEY environment variable or add api_key to config."
                )

            kwargs = {"api_key": api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url

            self._client = OpenAI(**kwargs)

        return self._client

    def is_configured(self) -> bool:
        """Check if the transcriber has a valid API key."""
        return bool(self.config.api_key)

    def get_configuration_error(self) -> str | None:
        """Get configuration error message if not configured."""
        if not self.config.api_key:
            return (
                "OpenAI API key not set. "
                "Export OPENAI_API_KEY or add it to config.toml"
            )
        return None

    def transcribe(self, file_path: Path) -> str:
        """
        Transcribe an audio file using OpenAI's API.

        For long recordings, the file is split into chunks and each chunk
        is transcribed separately, then concatenated.

        Args:
            file_path: Path to the audio file.

        Returns:
            The complete transcribed text.

        Raises:
            TranscriberError: If transcription fails.
        """
        if not file_path.exists():
            raise TranscriberError(f"Audio file not found: {file_path}")

        # Check if chunking is needed
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        duration_seconds = self._get_audio_duration(file_path)

        needs_chunking = (
            file_size_mb > self.config.max_chunk_mb
            or duration_seconds > self.config.max_chunk_seconds
        )

        if needs_chunking:
            return self._transcribe_chunked(file_path, duration_seconds)
        else:
            return self._transcribe_single(file_path)

    def _get_audio_duration(self, file_path: Path) -> float:
        """Get duration of a WAV file in seconds."""
        try:
            with wave.open(str(file_path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / rate
        except Exception as e:
            raise TranscriberError(f"Failed to read audio file: {e}") from e

    def _transcribe_single(self, file_path: Path) -> str:
        """Transcribe a single audio file."""
        client = self._get_client()

        try:
            with open(file_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=self.config.model,
                    file=audio_file,
                    response_format="text",
                )
            return response.strip() if isinstance(response, str) else response.text.strip()

        except APIConnectionError as e:
            raise TranscriberError(
                "Failed to connect to OpenAI API. Check your internet connection."
            ) from e
        except RateLimitError as e:
            raise TranscriberError(
                "OpenAI API rate limit exceeded. Please wait and try again."
            ) from e
        except APIError as e:
            raise TranscriberError(f"OpenAI API error: {e.message}") from e
        except Exception as e:
            raise TranscriberError(f"Transcription failed: {e}") from e

    def _transcribe_chunked(self, file_path: Path, total_duration: float) -> str:
        """
        Transcribe a long audio file by splitting into chunks.

        Args:
            file_path: Path to the audio file.
            total_duration: Total duration in seconds.

        Returns:
            Concatenated transcript from all chunks.
        """
        chunk_duration = self.config.max_chunk_seconds
        transcripts = []

        # Read the full audio file
        try:
            sample_rate, audio_data = wavfile.read(str(file_path))
        except Exception as e:
            raise TranscriberError(f"Failed to read audio file: {e}") from e

        # Ensure audio is 1D (mono)
        if len(audio_data.shape) > 1:
            audio_data = audio_data[:, 0]

        samples_per_chunk = int(chunk_duration * sample_rate)
        total_samples = len(audio_data)
        num_chunks = (total_samples + samples_per_chunk - 1) // samples_per_chunk

        for i in range(num_chunks):
            start_sample = i * samples_per_chunk
            end_sample = min((i + 1) * samples_per_chunk, total_samples)
            chunk_data = audio_data[start_sample:end_sample]

            # Write chunk to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                chunk_path = Path(tmp_file.name)

            try:
                wavfile.write(str(chunk_path), sample_rate, chunk_data)
                transcript = self._transcribe_single(chunk_path)
                if transcript:
                    transcripts.append(transcript)
            finally:
                # Clean up temporary chunk file
                try:
                    chunk_path.unlink()
                except Exception:
                    pass

        return " ".join(transcripts)


def create_transcriber(config: STTConfig) -> Transcriber:
    """
    Factory function to create a transcriber based on configuration.

    Args:
        config: STT configuration.

    Returns:
        A Transcriber instance.

    Raises:
        TranscriberError: If the configured provider is not supported.
    """
    if config.provider == "openai":
        return OpenAITranscriber(config)
    else:
        raise TranscriberError(
            f"Unknown STT provider: {config.provider}. "
            f"Supported providers: openai"
        )
