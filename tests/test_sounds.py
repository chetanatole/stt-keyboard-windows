"""Tests for mickey.sounds module."""

import winsound
from pathlib import Path

from mickey import sounds
from mickey.sounds import (
    play_sound,
    play_start_sound,
    play_stop_sound,
    reset_debounce,
    SOUNDS_DIR,
)

import pytest


@pytest.fixture(autouse=True)
def reset_sound_debounce():
    """Reset sound debounce before each test."""
    reset_debounce()
    yield
    reset_debounce()


class TestSoundPaths:
    def test_sounds_dir_exists(self):
        assert SOUNDS_DIR.exists(), f"Sounds directory not found: {SOUNDS_DIR}"

    def test_start_sound_exists(self):
        assert sounds.START_SOUND.exists(), f"Start sound not found: {sounds.START_SOUND}"

    def test_stop_sound_exists(self):
        assert sounds.STOP_SOUND.exists(), f"Stop sound not found: {sounds.STOP_SOUND}"

    def test_sound_files_have_wav_extension(self):
        assert sounds.START_SOUND.suffix == ".wav"
        assert sounds.STOP_SOUND.suffix == ".wav"


class TestPlaySound:
    def test_play_sound_calls_backend(self, mock_sound_backend):
        play_sound(sounds.START_SOUND)
        mock_sound_backend.assert_called_once()
        call_args = mock_sound_backend.call_args
        assert str(sounds.START_SOUND) in call_args[0][0]

    def test_play_sound_does_nothing_for_nonexistent_file(self, mock_sound_backend):
        nonexistent = Path("C:/nonexistent/sound.wav")
        play_sound(nonexistent)
        mock_sound_backend.assert_not_called()

    def test_play_sound_uses_async_flag(self, mock_sound_backend):
        play_sound(sounds.START_SOUND)
        call_args = mock_sound_backend.call_args
        flags = call_args[0][1]
        assert flags & winsound.SND_ASYNC
        assert flags & winsound.SND_FILENAME


class TestPlayStartSound:
    def test_play_start_sound_plays_correct_file(self, mock_sound_backend):
        play_start_sound()
        mock_sound_backend.assert_called_once()
        call_args = mock_sound_backend.call_args[0][0]
        assert "mic_unmute.wav" in str(call_args)


class TestPlayStopSound:
    def test_play_stop_sound_plays_correct_file(self, mock_sound_backend):
        play_stop_sound()
        mock_sound_backend.assert_called_once()
        call_args = mock_sound_backend.call_args[0][0]
        assert "mic_mute.wav" in str(call_args)
