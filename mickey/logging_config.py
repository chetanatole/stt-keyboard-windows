"""Logging configuration for STT Keyboard."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Log directory
LOG_DIR = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "STTKeyboard" / "Logs"
)
LOG_FILE = LOG_DIR / "app.log"

# Create logger
logger = logging.getLogger("stt-keyboard")
logger.setLevel(logging.DEBUG)

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# File handler with rotation (1MB max, keep 3 backups)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=1_000_000,  # 1MB
    backupCount=3,
    encoding="utf-8",
)
file_handler.setLevel(logging.DEBUG)

# Console handler (for development)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console

# Format: timestamp - level - message
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers
logger.addHandler(file_handler)
logger.addHandler(console_handler)


def get_logger(name: str = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional sub-logger name (e.g., 'typer', 'transcriber')

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"stt-keyboard.{name}")
    return logger
