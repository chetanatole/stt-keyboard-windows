"""Text input simulation module.

Windows text insertion via SendInput (default) or keystroke simulation.
"""

import time
from enum import Enum

from pynput.keyboard import Controller, Key

from .logging_config import get_logger

logger = get_logger("typer")


class InputMethod(Enum):
    """Available text input methods."""

    SENDINPUT = "sendinput"  # Win32 SendInput Unicode (default)
    KEYSTROKE = "keystroke"  # pynput keystroke simulation


class TextTyper:
    """Types text into the active application.

    Supports two input methods:
    - sendinput: Win32 SendInput with Unicode events (default)
    - keystroke: pynput keystroke simulation
    """

    CHUNK_SIZE = 20  # Maximum characters per event batch

    def __init__(
        self,
        typing_delay: float = 0.004,
        method: InputMethod = None,
    ):
        """Initialize the typer.

        Args:
            typing_delay: Delay between character chunks (default 4ms for reliability)
            method: The input method to use (default: SENDINPUT)
        """
        self._controller = Controller()
        self.typing_delay = typing_delay
        if method is None:
            self.method = InputMethod.SENDINPUT
        else:
            self.method = method

    def type_text(self, text: str) -> bool:
        """Type text into the active application.

        Args:
            text: The text to type

        Returns:
            True if text was inserted successfully, False otherwise
        """
        if not text:
            return True

        if self.method == InputMethod.KEYSTROKE:
            return self._type_via_keystroke(text)
        else:
            return self._type_via_sendinput(text)

    def _type_via_sendinput(self, text: str) -> bool:
        """Type text using Win32 SendInput with Unicode events.

        Each character is sent as a KEYEVENTF_UNICODE event pair (down + up).
        Text is processed in chunks with configurable delay between chunks.

        Args:
            text: The text to type

        Returns:
            True (always succeeds)
        """
        import ctypes
        from ctypes import wintypes

        # Constants
        INPUT_KEYBOARD = 1
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002

        # Structures — union must include MOUSEINPUT (largest member)
        # so ctypes.sizeof(INPUT) matches the Win32 INPUT struct size.
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [
                ("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class HARDWAREINPUT(ctypes.Structure):
            _fields_ = [
                ("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD),
            ]

        class INPUT(ctypes.Structure):
            class _INPUT(ctypes.Union):
                _fields_ = [
                    ("mi", MOUSEINPUT),
                    ("ki", KEYBDINPUT),
                    ("hi", HARDWAREINPUT),
                ]

            _fields_ = [
                ("type", wintypes.DWORD),
                ("_input", _INPUT),
            ]

        # Small delay to ensure focus is on the right window
        time.sleep(0.05)

        # Process text in chunks
        for i in range(0, len(text), self.CHUNK_SIZE):
            chunk = text[i : i + self.CHUNK_SIZE]

            # Build input events for each character
            inputs = []
            for char in chunk:
                code_point = ord(char)

                # Handle surrogate pairs for characters above BMP (emoji, etc.)
                if code_point > 0xFFFF:
                    high = 0xD800 + ((code_point - 0x10000) >> 10)
                    low = 0xDC00 + ((code_point - 0x10000) & 0x3FF)
                    surrogates = [high, low]
                else:
                    surrogates = [code_point]

                for scan_code in surrogates:
                    # Key down
                    inp_down = INPUT()
                    inp_down.type = INPUT_KEYBOARD
                    inp_down._input.ki.wVk = 0
                    inp_down._input.ki.wScan = scan_code
                    inp_down._input.ki.dwFlags = KEYEVENTF_UNICODE
                    inp_down._input.ki.time = 0
                    inp_down._input.ki.dwExtraInfo = None
                    inputs.append(inp_down)

                    # Key up
                    inp_up = INPUT()
                    inp_up.type = INPUT_KEYBOARD
                    inp_up._input.ki.wVk = 0
                    inp_up._input.ki.wScan = scan_code
                    inp_up._input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
                    inp_up._input.ki.time = 0
                    inp_up._input.ki.dwExtraInfo = None
                    inputs.append(inp_up)

            # Send all inputs for this chunk
            n_inputs = len(inputs)
            input_array = (INPUT * n_inputs)(*inputs)
            ctypes.windll.user32.SendInput(n_inputs, input_array, ctypes.sizeof(INPUT))

            if self.typing_delay > 0 and i + self.CHUNK_SIZE < len(text):
                time.sleep(self.typing_delay)

        return True

    def _type_via_keystroke(self, text: str) -> bool:
        """Type text using pynput keystroke simulation.

        Simpler but may trigger shortcuts in some apps.

        Args:
            text: The text to type

        Returns:
            True (always succeeds)
        """
        time.sleep(0.05)
        self._controller.type(text)
        return True

    def press_enter(self) -> None:
        """Press the Enter key."""
        self._controller.press(Key.enter)
        self._controller.release(Key.enter)
