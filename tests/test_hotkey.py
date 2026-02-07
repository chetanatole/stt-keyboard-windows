"""Tests for mickey.hotkey module."""

from unittest.mock import MagicMock, patch
from pynput import keyboard

from mickey.hotkey import HotkeyListener


class TestHotkeyListenerInit:
    def test_init_sets_defaults(self):
        listener = HotkeyListener()
        assert listener._on_press_callback is None
        assert listener._on_release_callback is None
        assert listener._listener is None
        assert listener._hotkey_active is False


class TestHotkeyListenerCallbacks:
    def test_set_callbacks(self):
        listener = HotkeyListener()
        press_cb = MagicMock()
        release_cb = MagicMock()
        listener.set_callbacks(press_cb, release_cb)
        assert listener._on_press_callback == press_cb
        assert listener._on_release_callback == release_cb


class TestIsHotkey:
    def test_is_hotkey_with_alt_r(self):
        listener = HotkeyListener()
        assert listener._is_hotkey(keyboard.Key.alt_r) is True

    def test_is_hotkey_with_alt_gr(self):
        listener = HotkeyListener()
        assert listener._is_hotkey(keyboard.Key.alt_gr) is True

    def test_is_hotkey_with_left_alt(self):
        listener = HotkeyListener()
        assert listener._is_hotkey(keyboard.Key.alt_l) is False
        assert listener._is_hotkey(keyboard.Key.alt) is False

    def test_is_hotkey_with_other_keys(self):
        listener = HotkeyListener()
        assert listener._is_hotkey(keyboard.Key.cmd) is False
        assert listener._is_hotkey(keyboard.Key.shift) is False
        assert listener._is_hotkey(keyboard.Key.ctrl) is False
        assert listener._is_hotkey(keyboard.Key.space) is False


class TestOnPress:
    def test_on_press_triggers_callback_for_hotkey(self):
        listener = HotkeyListener()
        press_cb = MagicMock()
        listener.set_callbacks(press_cb, MagicMock())
        listener._on_press(keyboard.Key.alt_r)
        press_cb.assert_called_once()
        assert listener._hotkey_active is True

    def test_on_press_does_not_retrigger_while_active(self):
        listener = HotkeyListener()
        press_cb = MagicMock()
        listener.set_callbacks(press_cb, MagicMock())
        listener._on_press(keyboard.Key.alt_r)
        listener._on_press(keyboard.Key.alt_r)
        listener._on_press(keyboard.Key.alt_r)
        assert press_cb.call_count == 1

    def test_on_press_ignores_non_hotkey(self):
        listener = HotkeyListener()
        press_cb = MagicMock()
        listener.set_callbacks(press_cb, MagicMock())
        listener._on_press(keyboard.Key.cmd)
        listener._on_press(keyboard.Key.shift)
        press_cb.assert_not_called()
        assert listener._hotkey_active is False

    def test_on_press_works_without_callback(self):
        listener = HotkeyListener()
        listener._on_press(keyboard.Key.alt_r)
        assert listener._hotkey_active is True


class TestOnRelease:
    def test_on_release_triggers_callback_when_active(self):
        listener = HotkeyListener()
        release_cb = MagicMock()
        listener.set_callbacks(MagicMock(), release_cb)
        listener._on_press(keyboard.Key.alt_r)
        listener._on_release(keyboard.Key.alt_r)
        release_cb.assert_called_once()
        assert listener._hotkey_active is False

    def test_on_release_does_nothing_when_not_active(self):
        listener = HotkeyListener()
        release_cb = MagicMock()
        listener.set_callbacks(MagicMock(), release_cb)
        listener._on_release(keyboard.Key.alt_r)
        release_cb.assert_not_called()

    def test_on_release_ignores_non_hotkey(self):
        listener = HotkeyListener()
        release_cb = MagicMock()
        listener.set_callbacks(MagicMock(), release_cb)
        listener._on_press(keyboard.Key.alt_r)
        listener._on_release(keyboard.Key.cmd)
        release_cb.assert_not_called()
        assert listener._hotkey_active is True

    def test_on_release_works_without_callback(self):
        listener = HotkeyListener()
        listener._hotkey_active = True
        listener._on_release(keyboard.Key.alt_r)
        assert listener._hotkey_active is False


class TestStartStop:
    @patch("mickey.hotkey.keyboard.Listener")
    def test_start_creates_listener(self, mock_listener_class):
        listener = HotkeyListener()
        listener.start()
        mock_listener_class.assert_called_once()
        mock_listener_class.return_value.start.assert_called_once()
        assert listener._listener is not None

    @patch("mickey.hotkey.keyboard.Listener")
    def test_stop_stops_listener(self, mock_listener_class):
        listener = HotkeyListener()
        listener.start()
        listener.stop()
        mock_listener_class.return_value.stop.assert_called_once()
        assert listener._listener is None

    def test_stop_does_nothing_when_not_started(self):
        listener = HotkeyListener()
        listener.stop()
        assert listener._listener is None


class TestPressReleaseCycle:
    def test_multiple_press_release_cycles(self):
        listener = HotkeyListener()
        press_cb = MagicMock()
        release_cb = MagicMock()
        listener.set_callbacks(press_cb, release_cb)

        for _ in range(3):
            listener._on_press(keyboard.Key.alt_r)
            listener._on_release(keyboard.Key.alt_r)

        assert press_cb.call_count == 3
        assert release_cb.call_count == 3
        assert listener._hotkey_active is False
