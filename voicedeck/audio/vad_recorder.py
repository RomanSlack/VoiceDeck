"""Continuous voice-activity-detection recorder for hot mic mode."""

import collections
import threading
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal


class VADRecorder(QObject):
    """Records audio segments based on voice activity detection.

    Continuously listens to the microphone and emits complete speech
    segments as WAV files when silence is detected after speech.

    Signals:
        segment_ready(Path): Emitted when a speech segment WAV file is ready.
        level_changed(float): Emitted with current RMS level (0.0-1.0).
    """

    segment_ready = Signal(Path)
    level_changed = Signal(float)

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        temp_dir: Optional[Path] = None,
        threshold: float = 0.02,
        silence_duration: float = 1.5,
        min_segment: float = 0.5,
        pre_speech_ms: int = 300,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)

        self.sample_rate = sample_rate
        self.channels = channels
        self.temp_dir = temp_dir or Path("/tmp/voicedeck_vad")
        self.threshold = threshold
        self.silence_duration = silence_duration
        self.min_segment = min_segment

        self._stream: Optional[sd.InputStream] = None
        self._lock = threading.Lock()
        self._is_listening = False

        # Pre-speech ring buffer: ~300ms of audio at 1024 samples/block
        pre_speech_blocks = max(1, int(
            (pre_speech_ms / 1000.0) * sample_rate / 1024
        ))
        self._ring_buffer: collections.deque[np.ndarray] = collections.deque(
            maxlen=pre_speech_blocks
        )

        # Speech accumulation state
        self._in_speech = False
        self._speech_frames: list[np.ndarray] = []
        self._silence_frames = 0
        self._silence_frames_needed = int(
            silence_duration * sample_rate / 1024
        )

    def start_listening(self, device_index: Optional[int] = None) -> None:
        """Start continuous VAD listening on the specified device."""
        if self._is_listening:
            return

        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self._stream = sd.InputStream(
            device=device_index,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=np.float32,
            callback=self._audio_callback,
            blocksize=1024,
        )

        self._is_listening = True
        self._in_speech = False
        self._speech_frames.clear()
        self._ring_buffer.clear()
        self._silence_frames = 0
        self._stream.start()

    def stop_listening(self) -> None:
        """Stop listening and fully release the microphone."""
        if not self._is_listening:
            return

        self._is_listening = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        # Discard any partial speech
        with self._lock:
            self._in_speech = False
            self._speech_frames.clear()
            self._ring_buffer.clear()

    @property
    def is_listening(self) -> bool:
        return self._is_listening

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Sounddevice callback — runs in audio thread."""
        if not self._is_listening:
            return

        audio = indata.copy()
        rms = float(np.sqrt(np.mean(audio ** 2)))
        level = min(1.0, rms * 4.0)
        self.level_changed.emit(level)

        is_voice = rms > self.threshold

        with self._lock:
            if not self._in_speech:
                # Always keep recent audio in ring buffer
                self._ring_buffer.append(audio)

                if is_voice:
                    # Speech started — flush ring buffer as pre-speech
                    self._in_speech = True
                    self._speech_frames = list(self._ring_buffer)
                    self._ring_buffer.clear()
                    self._speech_frames.append(audio)
                    self._silence_frames = 0
            else:
                # Currently in speech
                self._speech_frames.append(audio)

                if is_voice:
                    self._silence_frames = 0
                else:
                    self._silence_frames += 1

                    if self._silence_frames >= self._silence_frames_needed:
                        # Silence long enough — finalize segment
                        segment_frames = self._speech_frames
                        self._speech_frames = []
                        self._in_speech = False
                        self._silence_frames = 0

                        # Check minimum segment duration
                        total_samples = sum(f.shape[0] for f in segment_frames)
                        duration = total_samples / self.sample_rate
                        if duration >= self.min_segment:
                            self._write_segment(segment_frames)

    def _write_segment(self, frames: list[np.ndarray]) -> None:
        """Write accumulated speech frames to a WAV file and emit signal."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        path = self.temp_dir / f"vad_segment_{timestamp}.wav"

        try:
            audio = np.concatenate(frames, axis=0)
            audio_int16 = (audio * 32767).astype(np.int16)

            with wave.open(str(path), "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())

            self.segment_ready.emit(path)
        except Exception:
            # Don't crash the audio thread on write errors
            pass
