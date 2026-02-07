"""Tests for mickey.config module."""

import json
from unittest.mock import patch

from mickey.config import Config


class TestConfigDefaults:
    """Test Config default values."""

    def test_default_model_size(self):
        config = Config()
        assert config.model_size == "small"

    def test_default_language(self):
        config = Config()
        assert config.language == "en"

    def test_default_sample_rate(self):
        config = Config()
        assert config.sample_rate == 16000

    def test_default_channels(self):
        config = Config()
        assert config.channels == 1

    def test_default_compute_type(self):
        config = Config()
        assert config.compute_type == "int8"

    def test_default_play_sounds(self):
        config = Config()
        assert config.play_sounds is True

    def test_default_input_device(self):
        config = Config()
        assert config.input_device is None

    def test_default_initial_prompt(self):
        config = Config()
        assert "punctuation" in config.initial_prompt.lower()
        assert "capitalization" in config.initial_prompt.lower()

    def test_default_text_input_method(self):
        config = Config()
        assert config.text_input_method == "sendinput"

    def test_default_max_recording_duration(self):
        config = Config()
        assert config.max_recording_duration == 300


class TestConfigSaveLoad:
    """Test Config save and load functionality."""

    def test_save_creates_directory(self, tmp_path):
        """Test that save creates the config directory if it doesn't exist."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"

        with (
            patch("mickey.config.CONFIG_DIR", config_dir),
            patch("mickey.config.CONFIG_FILE", config_file),
        ):
            config = Config()
            config.save()

            assert config_dir.exists()
            assert config_file.exists()

    def test_save_writes_json(self, tmp_path):
        """Test that save writes valid JSON with correct values."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"

        with (
            patch("mickey.config.CONFIG_DIR", config_dir),
            patch("mickey.config.CONFIG_FILE", config_file),
        ):
            config = Config(model_size="large", language="es")
            config.save()

            with open(config_file) as f:
                data = json.load(f)

            assert data["model_size"] == "large"
            assert data["language"] == "es"

    def test_load_returns_defaults_when_no_file(self, tmp_path):
        """Test that load returns defaults when config file doesn't exist."""
        config_file = tmp_path / "nonexistent.json"

        with patch("mickey.config.CONFIG_FILE", config_file):
            config = Config.load()

            assert config.model_size == "small"
            assert config.language == "en"

    def test_load_reads_saved_config(self, tmp_path):
        """Test that load reads previously saved config."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)

        config_data = {
            "model_size": "medium",
            "language": "fr",
            "sample_rate": 16000,
            "channels": 1,
            "compute_type": "int8",
            "play_sounds": False,
            "input_device": "Test Mic",
            "initial_prompt": "Custom prompt",
        }
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        with patch("mickey.config.CONFIG_FILE", config_file):
            config = Config.load()

            assert config.model_size == "medium"
            assert config.language == "fr"
            assert config.play_sounds is False
            assert config.input_device == "Test Mic"
            assert config.initial_prompt == "Custom prompt"

    def test_load_handles_invalid_json(self, tmp_path):
        """Test that load returns defaults when JSON is invalid."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)

        with open(config_file, "w") as f:
            f.write("not valid json {{{")

        with patch("mickey.config.CONFIG_FILE", config_file):
            config = Config.load()
            assert config.model_size == "small"

    def test_load_handles_missing_fields(self, tmp_path):
        """Test that load handles config with missing fields."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"
        config_dir.mkdir(parents=True)

        with open(config_file, "w") as f:
            json.dump({"model_size": "tiny"}, f)

        with patch("mickey.config.CONFIG_FILE", config_file):
            config = Config.load()
            assert config is not None


class TestConfigRoundTrip:
    """Test Config save/load round-trip."""

    def test_roundtrip_preserves_values(self, tmp_path):
        """Test that saving and loading preserves all config values."""
        config_dir = tmp_path / ".config" / "stt-keyboard"
        config_file = config_dir / "config.json"

        with (
            patch("mickey.config.CONFIG_DIR", config_dir),
            patch("mickey.config.CONFIG_FILE", config_file),
        ):
            original = Config(
                model_size="large",
                language="de",
                sample_rate=44100,
                channels=2,
                compute_type="float16",
                play_sounds=False,
                input_device="USB Mic",
                initial_prompt="Test prompt",
                text_input_method="sendinput",
            )
            original.save()

            loaded = Config.load()

            assert loaded.model_size == original.model_size
            assert loaded.language == original.language
            assert loaded.sample_rate == original.sample_rate
            assert loaded.channels == original.channels
            assert loaded.compute_type == original.compute_type
            assert loaded.play_sounds == original.play_sounds
            assert loaded.input_device == original.input_device
            assert loaded.initial_prompt == original.initial_prompt
            assert loaded.text_input_method == original.text_input_method
