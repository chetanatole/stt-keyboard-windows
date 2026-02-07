"""Tests for mickey.typer module."""

from unittest.mock import patch, MagicMock

from mickey.typer import TextTyper, InputMethod


class TestInputMethodEnum:
    def test_sendinput_value(self):
        assert InputMethod.SENDINPUT.value == "sendinput"

    def test_keystroke_value(self):
        assert InputMethod.KEYSTROKE.value == "keystroke"

    def test_enum_from_string(self):
        assert InputMethod("sendinput") == InputMethod.SENDINPUT
        assert InputMethod("keystroke") == InputMethod.KEYSTROKE

    def test_invalid_value_raises(self):
        import pytest

        with pytest.raises(ValueError):
            InputMethod("invalid")


class TestTextTyperInit:
    def test_default_method(self):
        typer = TextTyper()
        assert typer.method == InputMethod.SENDINPUT

    def test_custom_method(self):
        typer = TextTyper(method=InputMethod.KEYSTROKE)
        assert typer.method == InputMethod.KEYSTROKE

    def test_default_typing_delay(self):
        typer = TextTyper()
        assert typer.typing_delay == 0.004

    def test_custom_typing_delay(self):
        typer = TextTyper(typing_delay=0.01)
        assert typer.typing_delay == 0.01

    def test_chunk_size_constant(self):
        assert TextTyper.CHUNK_SIZE == 20


class TestTextTyperTypeText:
    def test_empty_text_returns_true(self):
        typer = TextTyper()
        assert typer.type_text("") is True

    def test_none_text_returns_true(self):
        typer = TextTyper()
        assert typer.type_text(None) is True

    def test_sendinput_method_calls_sendinput(self):
        typer = TextTyper(method=InputMethod.SENDINPUT)
        with patch.object(typer, "_type_via_sendinput", return_value=True) as mock:
            typer.type_text("hello")
            mock.assert_called_once_with("hello")

    def test_keystroke_method_calls_keystroke(self):
        typer = TextTyper(method=InputMethod.KEYSTROKE)
        with patch.object(typer, "_type_via_keystroke", return_value=True) as mock:
            typer.type_text("hello")
            mock.assert_called_once_with("hello")


class TestSendInputTyping:
    @patch("mickey.typer.time.sleep")
    def test_type_via_sendinput_returns_true(self, mock_sleep):
        typer = TextTyper(method=InputMethod.SENDINPUT)
        with patch("ctypes.windll.user32.SendInput", return_value=2):
            result = typer._type_via_sendinput("Hi")
        assert result is True

    @patch("mickey.typer.time.sleep")
    def test_type_via_sendinput_calls_send_input(self, mock_sleep):
        typer = TextTyper(method=InputMethod.SENDINPUT)
        with patch("ctypes.windll.user32.SendInput") as mock_send:
            mock_send.return_value = 4
            typer._type_via_sendinput("Hi")
        mock_send.assert_called_once()
        assert mock_send.call_args[0][0] == 4

    @patch("mickey.typer.time.sleep")
    def test_type_via_sendinput_chunks_long_text(self, mock_sleep):
        typer = TextTyper(method=InputMethod.SENDINPUT, typing_delay=0)
        with patch("ctypes.windll.user32.SendInput") as mock_send:
            mock_send.return_value = 40
            typer._type_via_sendinput("A" * 50)
        assert mock_send.call_count == 3

    @patch("mickey.typer.time.sleep")
    def test_type_via_sendinput_sleeps_between_chunks(self, mock_sleep):
        typer = TextTyper(method=InputMethod.SENDINPUT, typing_delay=0.01)
        with patch("ctypes.windll.user32.SendInput") as mock_send:
            mock_send.return_value = 40
            typer._type_via_sendinput("A" * 30)
        sleep_calls = [c[0][0] for c in mock_sleep.call_args_list]
        assert 0.05 in sleep_calls
        assert 0.01 in sleep_calls

    @patch("mickey.typer.time.sleep")
    def test_type_via_sendinput_handles_emoji(self, mock_sleep):
        typer = TextTyper(method=InputMethod.SENDINPUT)
        with patch("ctypes.windll.user32.SendInput") as mock_send:
            mock_send.return_value = 4
            result = typer._type_via_sendinput("\U0001f600")
        assert result is True
        assert mock_send.call_args[0][0] == 4


class TestKeystrokeTyping:
    @patch("mickey.typer.time.sleep")
    def test_type_via_keystroke_uses_controller(self, mock_sleep):
        typer = TextTyper(method=InputMethod.KEYSTROKE)
        with patch.object(typer._controller, "type") as mock_type:
            result = typer._type_via_keystroke("hello")
        assert result is True
        mock_type.assert_called_once_with("hello")


class TestPressEnter:
    def test_press_enter_uses_pynput(self):
        typer = TextTyper()
        with (
            patch.object(typer._controller, "press") as mock_press,
            patch.object(typer._controller, "release") as mock_release,
        ):
            typer.press_enter()
            mock_press.assert_called_once()
            mock_release.assert_called_once()
