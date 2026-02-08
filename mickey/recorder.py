"""Audio recording module."""

import threading
import time

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from the microphone using callback-based streaming."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device: str | int | None = None,
        max_duration: int = 0,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.max_duration = max_duration  # 0 = unlimited
        self._recording = False
        self._audio_data: list[np.ndarray] = []
        self._current_level: float = 0.0  # Current audio level (0.0 - 1.0)
        self._stream: sd.InputStream | None = None
        self._cleanup_complete = threading.Event()
        self._cleanup_complete.set()  # Initially set (no cleanup pending)
        self._start_time: float = 0.0

    def start(self) -> None:
        """Start recording audio.

        Waits for any pending stream cleanup before starting a new recording
        to prevent device-busy errors.
        """
        # Wait for any pending cleanup to complete
        if not self._cleanup_complete.wait(timeout=0.5):
            import sys

            print(
                "Warning: Stream cleanup taking longer than expected",
                file=sys.stderr,
            )

        # Additional delay to let audio subsystem fully release resources.
        time.sleep(0.15)

        self._audio_data = []
        self._recording = True
        self._current_level = 0.0
        self._start_time = time.time()

        # Create and start a new stream for each recording
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32,
            device=self.device,
            callback=self._audio_callback,
            blocksize=512,  # Small blocks for responsive metering
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        """Stop recording and return audio data."""
        self._recording = False

        old_stream = self._stream
        self._stream = None

        # Schedule cleanup in a background thread to avoid blocking
        if old_stream is not None:
            self._cleanup_complete.clear()

            def cleanup():
                try:
                    old_stream.abort()
                    old_stream.close()
                except Exception:
                    pass
                finally:
                    self._cleanup_complete.set()

            t = threading.Thread(target=cleanup, daemon=True)
            t.start()

        # Grab the collected data
        data = self._audio_data
        self._audio_data = []

        if not data:
            return np.array([], dtype=np.float32)

        return np.concatenate(data, axis=0).flatten()

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info, status: sd.CallbackFlags
    ) -> None:
        """Callback for audio stream."""
        if self._recording:
            self._audio_data.append(indata.copy())
            # Calculate RMS level for visualization (normalized to 0-1)
            rms = np.sqrt(np.mean(indata**2))
            self._current_level = min(1.0, rms * 15)

    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording

    @property
    def current_level(self) -> float:
        """Get current audio level (0.0 - 1.0) for visualization."""
        return self._current_level

    @property
    def cleanup_pending(self) -> bool:
        """Check if stream cleanup is still in progress."""
        return not self._cleanup_complete.is_set()

    @property
    def exceeded_max_duration(self) -> bool:
        """Check if recording has exceeded max duration."""
        if not self._recording or self.max_duration <= 0:
            return False
        return (time.time() - self._start_time) >= self.max_duration
