#!/usr/bin/env python3
"""STT Keyboard - Speech-to-Text Tool

Entry point for the application.
"""

import ctypes
import os
import sys

from .config import CONFIG_DIR
from .logging_config import get_logger

# Set Windows AppUserModelID so Task Manager and taskbar show "STT Keyboard"
# instead of "Python". Must be called before any Qt imports.
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("STTKeyboard.STTKeyboard.App.1")

logger = get_logger("app")

# Lock file for single instance
LOCK_FILE = CONFIG_DIR / "app.lock"
_lock_fd = None


def acquire_lock() -> bool:
    """Acquire single-instance lock. Returns True if successful."""
    global _lock_fd
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        _lock_fd = open(LOCK_FILE, "w")
        import msvcrt

        msvcrt.locking(_lock_fd.fileno(), msvcrt.LK_NBLCK, 1)
        _lock_fd.write(str(os.getpid()))
        _lock_fd.flush()
        return True
    except (IOError, OSError):
        return False


def release_lock():
    """Release the single-instance lock."""
    global _lock_fd
    if _lock_fd:
        try:
            import msvcrt

            msvcrt.locking(_lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
            _lock_fd.close()
            LOCK_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        _lock_fd = None


def main():
    """Main entry point."""
    # Ensure single instance
    if not acquire_lock():
        print("STT Keyboard is already running.")
        logger.warning("Attempted to start second instance, exiting")
        sys.exit(0)

    try:
        logger.info("Starting STT Keyboard")
        print("Starting STT Keyboard...")
        print("Hold Right Alt to record, release to transcribe.")

        logger.info("Permissions OK, launching app")

        # ctranslate2 must be loaded BEFORE PyQt6 to avoid DLL conflicts
        # that cause segfaults on Windows. Pre-load the model here.
        from .config import config
        from .transcriber import Transcriber

        logger.info("Pre-loading Whisper model (before Qt)...")
        _preloaded_transcriber = Transcriber(
            model_size=config.model_size,
            compute_type=config.compute_type,
            language=config.language,
            initial_prompt=config.initial_prompt,
        )
        _preloaded_transcriber._ensure_model()
        logger.info("Whisper model loaded successfully")

        from .tray import MickeyApp

        app = MickeyApp(transcriber=_preloaded_transcriber)
        app.run()
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        raise
    finally:
        logger.info("STT Keyboard shutting down")
        release_lock()


if __name__ == "__main__":
    main()
