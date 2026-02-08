"""Global hotkey listener for push-to-talk."""

from pynput import keyboard
from typing import Callable, Optional


class HotkeyListener:
    """Listens for Right Option key for push-to-talk."""

    def __init__(self):
        self._on_press_callback: Optional[Callable[[], None]] = None
        self._on_release_callback: Optional[Callable[[], None]] = None
        self._listener: Optional[keyboard.Listener] = None
        self._hotkey_active = False

    def _is_hotkey(self, key) -> bool:
        """Check if key is the Right Alt key."""
        return key in (keyboard.Key.alt_r, keyboard.Key.alt_gr)

    def set_callbacks(
        self, on_press: Callable[[], None], on_release: Callable[[], None]
    ) -> None:
        """Set callbacks for hotkey press and release.

        Args:
            on_press: Called when hotkey is pressed (start recording)
            on_release: Called when hotkey is released (stop recording)
        """
        self._on_press_callback = on_press
        self._on_release_callback = on_release

    def _on_press(self, key) -> None:
        """Handle key press events."""
        if self._is_hotkey(key):
            if not self._hotkey_active:
                self._hotkey_active = True
                if self._on_press_callback:
                    self._on_press_callback()

    def _on_release(self, key) -> None:
        """Handle key release events."""
        if self._is_hotkey(key):
            if self._hotkey_active:
                self._hotkey_active = False
                if self._on_release_callback:
                    self._on_release_callback()

    def start(self) -> None:
        """Start listening for the hotkey."""
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release
        )
        self._listener.start()

    def stop(self) -> None:
        """Stop listening."""
        if self._listener:
            self._listener.stop()
            self._listener = None
