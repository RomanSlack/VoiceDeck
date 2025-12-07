"""Audio recording functionality using sounddevice."""

import threading
import wave
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


class RecorderError(Exception):
    """Exception raised for recording errors."""
    pass


@dataclass
class AudioDevice:
    """Represents an audio input device."""
    index: int
    name: str
    channels: int
    default_sample_rate: float

    def __str__(self) -> str:
        return self.name


class AudioRecorder:
    """
    Records audio from a microphone to a WAV file on disk.

    Audio is written incrementally to avoid memory issues with long recordings.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        temp_dir: Optional[Path] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.temp_dir = temp_dir or Path.home() / ".cache" / "voicedeck"

        self._stream: Optional[sd.InputStream] = None
        self._wav_file: Optional[wave.Wave_write] = None
        self._current_file: Optional[Path] = None
        self._is_recording = False
        self._lock = threading.Lock()
        self._error_callback: Optional[Callable[[str], None]] = None

    @staticmethod
    def list_devices() -> list[AudioDevice]:
        """List all available audio input devices."""
        devices = []
        try:
            device_list = sd.query_devices()
            for i, dev in enumerate(device_list):
                # Only include input devices (max_input_channels > 0)
                if dev.get("max_input_channels", 0) > 0:
                    devices.append(
                        AudioDevice(
                            index=i,
                            name=dev["name"],
                            channels=dev["max_input_channels"],
                            default_sample_rate=dev["default_samplerate"],
                        )
                    )
        except Exception as e:
            raise RecorderError(f"Failed to list audio devices: {e}") from e

        return devices

    @staticmethod
    def get_default_device() -> Optional[AudioDevice]:
        """Get the default input device."""
        try:
            default_idx = sd.default.device[0]  # Input device index
            if default_idx is None or default_idx < 0:
                devices = AudioRecorder.list_devices()
                return devices[0] if devices else None

            dev = sd.query_devices(default_idx)
            if dev.get("max_input_channels", 0) > 0:
                return AudioDevice(
                    index=default_idx,
                    name=dev["name"],
                    channels=dev["max_input_channels"],
                    default_sample_rate=dev["default_samplerate"],
                )
        except Exception:
            pass

        # Fallback: return first available input device
        devices = AudioRecorder.list_devices()
        return devices[0] if devices else None

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback to be called when an error occurs during recording."""
        self._error_callback = callback

    def _generate_filename(self) -> Path:
        """Generate a unique filename for the recording."""
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.temp_dir / f"recording_{timestamp}.wav"

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time_info: dict,
        status: sd.CallbackFlags,
    ) -> None:
        """Callback function called for each audio block."""
        if status and self._error_callback:
            self._error_callback(f"Audio status: {status}")

        with self._lock:
            if self._wav_file is not None and self._is_recording:
                # Convert float32 to int16 for WAV file
                audio_data = (indata * 32767).astype(np.int16)
                self._wav_file.writeframes(audio_data.tobytes())

    def start(self, device: Optional[AudioDevice] = None) -> Path:
        """
        Start recording audio from the specified device.

        Args:
            device: The audio device to record from. Uses default if None.

        Returns:
            Path to the output WAV file.

        Raises:
            RecorderError: If recording cannot be started.
        """
        if self._is_recording:
            raise RecorderError("Already recording")

        if device is None:
            device = self.get_default_device()
            if device is None:
                raise RecorderError("No audio input devices available")

        # Verify device is still valid
        try:
            sd.query_devices(device.index)
        except Exception as e:
            raise RecorderError(f"Selected device is not available: {e}") from e

        self._current_file = self._generate_filename()

        try:
            # Open WAV file for writing
            self._wav_file = wave.open(str(self._current_file), "wb")
            self._wav_file.setnchannels(self.channels)
            self._wav_file.setsampwidth(2)  # 16-bit audio
            self._wav_file.setframerate(self.sample_rate)

            # Create and start the input stream
            self._stream = sd.InputStream(
                device=device.index,
                channels=self.channels,
                samplerate=self.sample_rate,
                dtype=np.float32,
                callback=self._audio_callback,
                blocksize=1024,
            )

            self._is_recording = True
            self._stream.start()

        except sd.PortAudioError as e:
            self._cleanup()
            if "Invalid device" in str(e):
                raise RecorderError(f"Device not available: {device.name}") from e
            elif "permission" in str(e).lower():
                raise RecorderError(
                    "Microphone access denied. Check system permissions."
                ) from e
            else:
                raise RecorderError(f"Audio error: {e}") from e
        except Exception as e:
            self._cleanup()
            raise RecorderError(f"Failed to start recording: {e}") from e

        return self._current_file

    def stop(self) -> Optional[Path]:
        """
        Stop recording and finalize the audio file.

        Returns:
            Path to the recorded WAV file, or None if not recording.
        """
        if not self._is_recording:
            return None

        with self._lock:
            self._is_recording = False

        # Stop and close stream
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        # Close WAV file
        if self._wav_file is not None:
            try:
                self._wav_file.close()
            except Exception:
                pass
            self._wav_file = None

        result = self._current_file
        self._current_file = None
        return result

    def _cleanup(self) -> None:
        """Clean up resources on error."""
        self._is_recording = False

        if self._stream is not None:
            try:
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        if self._wav_file is not None:
            try:
                self._wav_file.close()
            except Exception:
                pass
            self._wav_file = None

        if self._current_file is not None and self._current_file.exists():
            try:
                self._current_file.unlink()
            except Exception:
                pass
            self._current_file = None

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording

    @property
    def current_file(self) -> Optional[Path]:
        """Get the path to the current recording file."""
        return self._current_file
