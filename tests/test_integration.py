"""Integration tests for mickey app components."""

import numpy as np
from unittest.mock import MagicMock, patch


class TestHotkeyTranscriberIntegration:
    def test_hotkey_callbacks_trigger_transcription_flow(self):
        from mickey.hotkey import HotkeyListener
        from pynput import keyboard

        state = {"recording": False, "transcribed": False}

        def on_press():
            state["recording"] = True

        def on_release():
            state["recording"] = False
            state["transcribed"] = True

        listener = HotkeyListener()
        listener.set_callbacks(on_press, on_release)

        listener._on_press(keyboard.Key.alt_r)
        assert state["recording"] is True

        listener._on_release(keyboard.Key.alt_r)
        assert state["recording"] is False
        assert state["transcribed"] is True


class TestConfigTranscriberIntegration:
    def test_transcriber_uses_config_values(self):
        from mickey.config import Config
        from mickey.transcriber import Transcriber

        config = Config(
            model_size="small", language="fr",
            compute_type="int8", initial_prompt="Test prompt",
        )

        transcriber = Transcriber(
            model_size=config.model_size, language=config.language,
            compute_type=config.compute_type, initial_prompt=config.initial_prompt,
        )

        assert transcriber.model_size == "small"
        assert transcriber.language == "fr"
        assert transcriber.compute_type == "int8"
        assert transcriber.initial_prompt == "Test prompt"


class TestSoundsIntegration:
    def test_sounds_can_be_played_without_error(self, mock_sound_backend):
        from mickey.sounds import play_start_sound, play_stop_sound, reset_debounce

        reset_debounce()
        play_start_sound()
        reset_debounce()
        play_stop_sound()


class TestRecorderTranscriberIntegration:
    def test_audio_format_compatibility(self):
        from mickey.transcriber import Transcriber

        audio = np.random.randn(16000).astype(np.float32)

        with patch("faster_whisper.WhisperModel") as mock_whisper:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = ([MagicMock(text="Test")], MagicMock())
            mock_whisper.return_value = mock_model

            transcriber = Transcriber()
            result = transcriber.transcribe(audio)
            assert isinstance(result, str)


class TestComponentCallbackChain:
    def test_full_callback_chain(self):
        from mickey.hotkey import HotkeyListener
        from pynput import keyboard

        events = []
        listener = HotkeyListener()
        listener.set_callbacks(lambda: events.append("press"), lambda: events.append("release"))

        listener._on_press(keyboard.Key.alt_r)
        listener._on_release(keyboard.Key.alt_r)
        assert events == ["press", "release"]

    def test_multiple_cycles(self):
        from mickey.hotkey import HotkeyListener
        from pynput import keyboard

        cycles = []
        listener = HotkeyListener()
        listener.set_callbacks(lambda: cycles.append("start"), lambda: cycles.append("stop"))

        for _ in range(5):
            listener._on_press(keyboard.Key.alt_r)
            listener._on_release(keyboard.Key.alt_r)

        assert cycles == ["start", "stop"] * 5
