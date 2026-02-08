"""Pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".config" / "stt-keyboard"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def temp_config_file(temp_config_dir):
    """Create a temporary config file path."""
    return temp_config_dir / "config.json"


@pytest.fixture
def mock_whisper_model():
    """Mock the WhisperModel for transcriber tests."""
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Hello world"
    mock_model.transcribe.return_value = ([mock_segment], MagicMock())
    return mock_model


@pytest.fixture
def mock_keyboard_listener():
    """Mock pynput keyboard listener."""
    with patch("pynput.keyboard.Listener") as mock:
        yield mock


@pytest.fixture
def mock_sound_backend():
    """Mock winsound backend."""
    with patch("winsound.PlaySound") as mock:
        yield mock
