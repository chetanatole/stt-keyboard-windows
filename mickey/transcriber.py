"""Speech-to-text transcription using faster-whisper."""

import numpy as np

from .logging_config import get_logger

logger = get_logger("transcriber")


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""

    pass


def _detect_device() -> tuple[str, str]:
    """Detect best available device and compute type.

    Returns:
        (device, compute_type) tuple, e.g. ("cuda", "float16") or ("cpu", "int8")
    """
    try:
        import ctranslate2

        ctranslate2.get_supported_compute_types("cuda")
        logger.info("CUDA is available, using GPU")
        return "cuda", "float16"
    except Exception as e:
        logger.info("CUDA not available (%s), using CPU", e)
        return "cpu", "int8"


class Transcriber:
    """Transcribes audio to text using Whisper."""

    def __init__(
        self,
        model_size: str = "base",
        compute_type: str = "int8",
        device: str = "auto",
        language: str = "en",
        initial_prompt: str = "",
    ):
        self.model_size = model_size
        self.language = language
        self.initial_prompt = initial_prompt
        self._model = None

        if device == "auto":
            self.device, self.compute_type = _detect_device()
        else:
            self.device = device
            self.compute_type = compute_type

    def _ensure_model(self) -> None:
        """Lazy load the Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(
                    "Loading model '%s' on %s (compute_type=%s)",
                    self.model_size,
                    self.device,
                    self.compute_type,
                )
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
                logger.info("Model loaded successfully on %s", self.device)
            except Exception as e:
                if self.device == "cuda":
                    logger.warning(
                        "Failed to load model on CUDA (%s), falling back to CPU", e
                    )
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self._model = WhisperModel(
                        self.model_size,
                        device="cpu",
                        compute_type=self.compute_type,
                    )
                    logger.info("Model loaded successfully on CPU (fallback)")
                else:
                    raise TranscriptionError(
                        f"Failed to load Whisper model: {e}"
                    ) from e

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
