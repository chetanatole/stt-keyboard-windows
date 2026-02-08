"""Sound feedback for Mickey."""

import time
import winsound
from pathlib import Path

# Bundled sounds directory (relative to this module)
SOUNDS_DIR = Path(__file__).parent / "sounds"

# Sound files
START_SOUND = SOUNDS_DIR / "mic_unmute.wav"
STOP_SOUND = SOUNDS_DIR / "mic_mute.wav"

# Debounce settings
_DEBOUNCE_INTERVAL = 0.1  # Minimum seconds between sound plays
_last_sound_time: float = 0.0


def reset_debounce() -> None:
    """Reset the debounce timer (for testing)."""
    global _last_sound_time
    _last_sound_time = 0.0


def play_sound(sound_path: Path) -> None:
    """Play a sound file asynchronously with debouncing.

    Prevents spawning many sound processes on rapid toggles.
    """
    global _last_sound_time

    now = time.time()
    if now - _last_sound_time < _DEBOUNCE_INTERVAL:
        return  # Skip if too soon after last sound

    if sound_path.exists():
        winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        _last_sound_time = now


def play_start_sound() -> None:
    """Play sound when recording starts."""
    play_sound(START_SOUND)


def play_stop_sound() -> None:
    """Play sound when recording stops."""
    play_sound(STOP_SOUND)
