"""Speech-to-text transcription using faster-whisper."""

import numpy as np


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""

    pass


class Transcriber:
    """Transcribes audio to text using Whisper."""

    def __init__(
        self,
        model_size: str = "base",
        compute_type: str = "int8",
        language: str = "en",
        initial_prompt: str = "",
    ):
        self.model_size = model_size
        self.compute_type = compute_type
        self.language = language
        self.initial_prompt = initial_prompt
        self._model = None

    def _ensure_model(self) -> None:
        """Lazy load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_size, device="cpu", compute_type=self.compute_type
                )
            except Exception as e:
                raise TranscriptionError(f"Failed to load Whisper model: {e}") from e

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text.

        Args:
            audio: Audio data as numpy array (float32, 16kHz mono)

        Returns:
            Transcribed text
        """
        if len(audio) == 0:
            return ""

        self._ensure_model()

        try:
            segments, info = self._model.transcribe(
                audio,
                language=self.language,
                beam_size=5,
                vad_filter=True,
                initial_prompt=self.initial_prompt or None,
            )

            text = " ".join(segment.text.strip() for segment in segments)
            return text.strip()
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e
