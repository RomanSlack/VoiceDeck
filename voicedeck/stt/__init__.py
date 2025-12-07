"""Speech-to-text backend module."""

from .base import Transcriber, TranscriberError
from .openai_client import OpenAITranscriber

__all__ = ["Transcriber", "TranscriberError", "OpenAITranscriber"]
