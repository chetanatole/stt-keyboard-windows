"""Configuration for Mickey."""

import os
from dataclasses import dataclass
from pathlib import Path
import json

CONFIG_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "stt-keyboard"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    """Mickey configuration."""

    model_size: str = "small"
    language: str = "en"
    sample_rate: int = 16000
    channels: int = 1
    compute_type: str = "int8"
    # Device for inference: "auto" (detect GPU), "cuda", or "cpu"
    device: str = "auto"
    play_sounds: bool = True
    input_device: str | int | None = (
        None  # None=default, int=device index, str=device name
    )
    initial_prompt: str = (
        "Transcription of voice dictation for emails, messages, code comments, "
        "and notes. Uses proper punctuation, capitalization, and natural sentence structure."
    )
    # Text input method: "sendinput" (default) or "keystroke"
    text_input_method: str = "sendinput"
    # Max recording duration in seconds (0 = unlimited)
    max_recording_duration: int = 300

    def save(self) -> None:
        """Save config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls) -> "Config":
        """Load config from file, or return defaults."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()


# Global config instance
config = Config.load()
