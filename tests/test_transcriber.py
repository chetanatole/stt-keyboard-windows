"""Tests for mickey.transcriber module."""

import numpy as np
from unittest.mock import MagicMock, patch

from mickey.transcriber import Transcriber, _detect_device


class TestDetectDevice:
    def test_detect_device_with_cuda(self):
        with patch("ctranslate2.get_supported_compute_types", return_value={"float16", "int8"}):
            device, compute = _detect_device()
            assert device == "cuda"
            assert compute == "float16"

    def test_detect_device_without_cuda(self):
        with patch("ctranslate2.get_supported_compute_types", side_effect=RuntimeError("no CUDA")):
            device, compute = _detect_device()
            assert device == "cpu"
            assert compute == "int8"


class TestTranscriberInit:
    def test_init_with_defaults(self):
        with patch("mickey.transcriber._detect_device", return_value=("cpu", "int8")):
            transcriber = Transcriber()
        assert transcriber.model_size == "base"
        assert transcriber.device == "cpu"
        assert transcriber.compute_type == "int8"
        assert transcriber.language == "en"
        assert transcriber.initial_prompt == ""
        assert transcriber._model is None

    def test_init_with_explicit_device(self):
        transcriber = Transcriber(
            model_size="large", compute_type="float16",
            device="cuda", language="es", initial_prompt="Custom prompt",
        )
        assert transcriber.model_size == "large"
        assert transcriber.device == "cuda"
        assert transcriber.compute_type == "float16"
        assert transcriber.language == "es"
        assert transcriber.initial_prompt == "Custom prompt"

    def test_init_auto_detects_device(self):
        with patch("mickey.transcriber._detect_device", return_value=("cuda", "float16")):
            transcriber = Transcriber(device="auto")
        assert transcriber.device == "cuda"
        assert transcriber.compute_type == "float16"

    def test_model_is_lazy_loaded(self):
        transcriber = Transcriber(device="cpu")
        assert transcriber._model is None


class TestEnsureModel:
    def test_ensure_model_loads_model(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper:
            transcriber = Transcriber(model_size="small", compute_type="int8", device="cpu")
            transcriber._ensure_model()
            mock_whisper.assert_called_once_with("small", device="cpu", compute_type="int8")
            assert transcriber._model is not None

    def test_ensure_model_only_loads_once(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper:
            transcriber = Transcriber(device="cpu")
            transcriber._ensure_model()
            transcriber._ensure_model()
            transcriber._ensure_model()
            assert mock_whisper.call_count == 1

    def test_ensure_model_cuda_fallback_to_cpu(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper:
            mock_whisper.side_effect = [RuntimeError("CUDA error"), MagicMock()]
            transcriber = Transcriber(device="cuda", compute_type="float16")
            transcriber._ensure_model()
            assert transcriber.device == "cpu"
            assert transcriber.compute_type == "int8"
            assert mock_whisper.call_count == 2


class TestTranscribe:
    def test_transcribe_empty_audio_returns_empty_string(self):
        transcriber = Transcriber(device="cpu")
        result = transcriber.transcribe(np.array([]))
        assert result == ""
        assert transcriber._model is None

    def test_transcribe_calls_model(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_segment = MagicMock()
            mock_segment.text = "Hello world"
            mock_model.transcribe.return_value = ([mock_segment], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(language="en", device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            transcriber.transcribe(audio)

            mock_model.transcribe.assert_called_once()
            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs["language"] == "en"
            assert call_kwargs["beam_size"] == 5
            assert call_kwargs["vad_filter"] is True

    def test_transcribe_returns_text(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_segment = MagicMock()
            mock_segment.text = "  Hello world  "
            mock_model.transcribe.return_value = ([mock_segment], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            result = transcriber.transcribe(audio)
            assert result == "Hello world"

    def test_transcribe_joins_multiple_segments(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_segments = [
                MagicMock(text="Hello"),
                MagicMock(text="world"),
                MagicMock(text="test"),
            ]
            mock_model.transcribe.return_value = (mock_segments, MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            result = transcriber.transcribe(audio)
            assert result == "Hello world test"

    def test_transcribe_uses_initial_prompt(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(initial_prompt="Test prompt", device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            transcriber.transcribe(audio)

            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs["initial_prompt"] == "Test prompt"

    def test_transcribe_passes_none_for_empty_prompt(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(initial_prompt="", device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            transcriber.transcribe(audio)

            call_kwargs = mock_model.transcribe.call_args[1]
            assert call_kwargs["initial_prompt"] is None

    def test_transcribe_handles_empty_segments(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            result = transcriber.transcribe(audio)
            assert result == ""


class TestTranscriberIntegration:
    def test_multiple_transcriptions_reuse_model(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text="Test")], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            transcriber.transcribe(audio)
            transcriber.transcribe(audio)
            transcriber.transcribe(audio)

            assert mock_whisper_class.call_count == 1
            assert mock_model.transcribe.call_count == 3

    def test_initial_prompt_can_be_updated(self):
        with patch("faster_whisper.WhisperModel") as mock_whisper_class:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text="Test")], MagicMock())
            mock_whisper_class.return_value = mock_model

            transcriber = Transcriber(initial_prompt="First prompt", device="cpu")
            audio = np.random.randn(16000).astype(np.float32)
            transcriber.transcribe(audio)
            transcriber.initial_prompt = "Second prompt"
            transcriber.transcribe(audio)

            calls = mock_model.transcribe.call_args_list
            assert calls[0][1]["initial_prompt"] == "First prompt"
            assert calls[1][1]["initial_prompt"] == "Second prompt"
