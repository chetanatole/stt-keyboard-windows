"""Permission checking and requesting (Windows)."""

import os


def check_accessibility_permission() -> bool:
    """Check if Accessibility permission is granted.

    On Windows, this is always True (no such concept).
    """
    return True


def check_microphone_permission() -> bool:
    """Check if Microphone permission is granted."""
    try:
        import sounddevice as sd

        sd.check_input_settings()
        return True
    except Exception:
        return False


def request_microphone_permission() -> None:
    """Request microphone permission from the user."""
    open_microphone_preferences()


def open_accessibility_preferences() -> None:
    """No-op on Windows."""
    pass


def open_microphone_preferences() -> None:
    """Open Windows Settings for microphone privacy."""
    os.startfile("ms-settings:privacy-microphone")


def check_all_permissions() -> tuple[bool, bool]:
    """Check all required permissions.

    Returns:
        Tuple of (accessibility_ok, microphone_ok)
    """
    return check_accessibility_permission(), check_microphone_permission()
