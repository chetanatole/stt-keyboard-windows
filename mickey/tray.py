"""System tray application for Mickey (PyQt6)."""

import sounddevice as sd
import threading
import time

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMenu,
    QPlainTextEdit,
    QSystemTrayIcon,
    QVBoxLayout,
)

from .recorder import AudioRecorder
from .transcriber import Transcriber, TranscriptionError
from .typer import TextTyper, InputMethod
from .hotkey import HotkeyListener
from .config import config
from .sounds import play_start_sound, play_stop_sound
from .permissions import (
    check_microphone_permission,
    open_microphone_preferences,
    request_microphone_permission,
)
from .indicator import get_indicator
from .logging_config import get_logger

logger = get_logger("tray")


class _TranscriptionSignals(QObject):
    """Signals for thread-safe communication from transcription thread."""

    finished = pyqtSignal(str)  # transcribed text
    error = pyqtSignal(str)  # error message


class MickeyApp:
    """Mickey system tray application."""

    def __init__(self, transcriber=None):
        # Create QApplication if not already running
        self.qt_app = QApplication.instance()
        if self.qt_app is None:
            import sys

            self.qt_app = QApplication(sys.argv)

        # Tray apps have no main window; prevent Qt from quitting when
        # dialogs (e.g. Edit Transcription Prompt) are closed.
        self.qt_app.setQuitOnLastWindowClosed(False)

        # System tray icon
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self._make_icon("M"))
        self.tray.setToolTip("STT Keyboard - Ready")

        # Components
        self.recorder = AudioRecorder(
            sample_rate=config.sample_rate,
            channels=config.channels,
            device=config.input_device,
            max_duration=config.max_recording_duration,
        )
        if transcriber is not None:
            self.transcriber = transcriber
        else:
            self.transcriber = Transcriber(
                model_size=config.model_size,
                compute_type=config.compute_type,
                language=config.language,
                initial_prompt=config.initial_prompt,
            )
        input_method = InputMethod(config.text_input_method)
        self.typer = TextTyper(method=input_method)
        self.hotkey = HotkeyListener()

        # State
        self._is_recording = False
        self._is_processing = False
        self._pending_start = False
        self._pending_stop = False
        self._last_stop_time = 0.0

        # Visual indicator
        self.indicator = get_indicator()

        # Build menu
        self._build_menu()

        # Set up hotkey callbacks
        self.hotkey.set_callbacks(
            on_press=self._on_hotkey_press, on_release=self._on_hotkey_release
        )

        # Signals for thread-safe GUI updates from transcription thread
        self._signals = _TranscriptionSignals()
        self._signals.finished.connect(self._on_transcription_finished)
        self._signals.error.connect(self._on_transcription_error)

        # Timer for pending actions (runs on main thread)
        self._main_timer = QTimer()
        self._main_timer.timeout.connect(self._check_pending_actions)
        self._main_timer.start(20)  # 20ms poll interval

    def _make_icon(self, letter: str) -> QIcon:
        """Create a simple text-based icon for the system tray."""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background circle
        if letter == "R":
            painter.setBrush(QColor(220, 50, 50))  # Red for recording
        elif letter == "P":
            painter.setBrush(QColor(255, 153, 0))  # Orange for processing
        else:
            painter.setBrush(QColor(80, 80, 80))  # Gray for ready

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 28, 28)

        # Draw letter
        font = QFont("Arial", 16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()
        return QIcon(pixmap)

    def _build_menu(self):
        """Build the system tray context menu."""
        menu = QMenu()

        # Status
        self.status_action = menu.addAction("Status: Ready")
        self.status_action.setEnabled(False)

        menu.addSeparator()

        # Input Device submenu
        self.device_menu = menu.addMenu("Input Device")
        self._populate_device_menu()

        # Text Input Method submenu
        self.method_menu = menu.addMenu("Text Input Method")
        self._populate_method_menu()

        # Edit Transcription Prompt
        edit_prompt_action = menu.addAction("Edit Transcription Prompt")
        edit_prompt_action.triggered.connect(self._edit_prompt)

        # Play Sounds toggle
        self.play_sounds_action = menu.addAction("Play Sounds")
        self.play_sounds_action.setCheckable(True)
        self.play_sounds_action.setChecked(config.play_sounds)
        self.play_sounds_action.triggered.connect(self._toggle_play_sounds)

        menu.addSeparator()

        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit_app)

        self.tray.setContextMenu(menu)

    def _populate_device_menu(self):
        """Populate the input device submenu."""
        self.device_menu.clear()
        devices = sd.query_devices()
        current_device = config.input_device
        default_device = sd.query_devices(kind="input")

        for i, device in enumerate(devices):
            if device["max_input_channels"] > 0:
                name = device["name"]
                action = self.device_menu.addAction(name)
                action.setCheckable(True)

                if current_device == name or current_device == i:
                    action.setChecked(True)
                elif current_device is None and device == default_device:
                    action.setChecked(True)

                action.triggered.connect(
                    lambda checked, n=name: self._select_input_device(n)
                )

        self.device_menu.addSeparator()
        hint = self.device_menu.addAction("Restart app to detect new devices")
        hint.setEnabled(False)

    def _populate_method_menu(self):
        """Populate the text input method submenu."""
        self.method_menu.clear()
        current_method = config.text_input_method

        sendinput_action = self.method_menu.addAction("SendInput (Default)")
        sendinput_action.setCheckable(True)
        sendinput_action.setChecked(current_method == "sendinput")
        sendinput_action.triggered.connect(
            lambda: self._select_input_method("sendinput", "SendInput")
        )

        keystroke_action = self.method_menu.addAction("Keystroke Simulation")
        keystroke_action.setCheckable(True)
        keystroke_action.setChecked(current_method == "keystroke")
        keystroke_action.triggered.connect(
            lambda: self._select_input_method("keystroke", "Keystroke")
        )

    def _select_input_device(self, device_name: str):
        """Handle input device selection."""
        config.input_device = device_name
        config.save()
        self.recorder.device = device_name

        for action in self.device_menu.actions():
            if action.isCheckable():
                action.setChecked(action.text() == device_name)

        self.tray.showMessage(
            "STT Keyboard",
            f"Input device set to: {device_name}",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _select_input_method(self, method: str, method_name: str):
        """Handle text input method selection."""
        config.text_input_method = method
        config.save()
        self.typer.method = InputMethod(method)

        for action in self.method_menu.actions():
            if action.isCheckable():
                if "SendInput" in action.text():
                    action.setChecked(method == "sendinput")
                elif "Keystroke" in action.text():
                    action.setChecked(method == "keystroke")

        self.tray.showMessage(
            "STT Keyboard",
            f"Text input method set to: {method_name}",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _toggle_play_sounds(self, checked: bool):
        """Toggle sound playback on/off."""
        config.play_sounds = checked
        config.save()

        status = "enabled" if config.play_sounds else "disabled"
        self.tray.showMessage(
            "STT Keyboard",
            f"Sound playback {status}",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _edit_prompt(self):
        """Show dialog to edit the transcription prompt."""
        dialog = QDialog()
        dialog.setWindowTitle("Edit Transcription Prompt")
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        dialog.resize(500, 250)

        layout = QVBoxLayout(dialog)
        label = QLabel(
            "This prompt conditions the Whisper model for better transcription.\n"
            "Use it to specify terminology, style, or context."
        )
        layout.addWidget(label)

        text_edit = QPlainTextEdit()
        text_edit.setPlainText(config.initial_prompt)
        layout.addWidget(text_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_prompt = text_edit.toPlainText().strip()
            config.initial_prompt = new_prompt
            config.save()
            self.transcriber.initial_prompt = new_prompt
            self.tray.showMessage(
                "STT Keyboard",
                "Transcription prompt updated.",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )

    def _on_hotkey_press(self) -> None:
        """Handle hotkey press (called from pynput thread)."""
        if self._is_recording or self._is_processing:
            return
        if time.time() - self._last_stop_time < 0.15:
            return
        self._pending_start = True

    def _on_hotkey_release(self) -> None:
        """Handle hotkey release (called from pynput thread)."""
        if self._is_recording or self._pending_start:
            self._pending_stop = True

    def _check_pending_actions(self) -> None:
        """Check for pending actions (runs on main thread via QTimer)."""
        if self._pending_start:
            self._pending_start = False
            self._do_start_recording()

        if self._pending_stop:
            self._pending_stop = False
            self._do_stop_recording()

        if self._is_recording:
            self.indicator.update_audio_level(self.recorder.current_level)
            if self.recorder.exceeded_max_duration:
                self._pending_stop = True
                self.tray.showMessage(
                    "STT Keyboard",
                    "Max recording duration reached",
                    QSystemTrayIcon.MessageIcon.Warning,
                    2000,
                )
        self.indicator.update_animation()

    def _do_start_recording(self) -> None:
        """Actually start recording (must run on main thread)."""
        if self._is_recording or self._is_processing:
            return

        if not check_microphone_permission():
            logger.warning("Microphone permission not granted")
            request_microphone_permission()
            self.tray.showMessage(
                "STT Keyboard",
                "Please grant microphone access in Settings and try again.",
                QSystemTrayIcon.MessageIcon.Warning,
                3000,
            )
            open_microphone_preferences()
            return

        logger.info("Starting recording")
        self._is_recording = True
        self._last_stop_time = 0
        self.tray.setIcon(self._make_icon("R"))
        self.tray.setToolTip("STT Keyboard - Recording...")
        self.status_action.setText("Status: Recording...")
        self.indicator.show_recording()
        if config.play_sounds:
            play_start_sound()
        try:
            self.recorder.start()
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self._is_recording = False
            self.tray.setIcon(self._make_icon("M"))
            self.tray.setToolTip("STT Keyboard - Ready")
            self.status_action.setText("Status: Ready")
            self.indicator.hide()
            self.tray.showMessage(
                "STT Keyboard",
                f"Could not start recording: {e}",
                QSystemTrayIcon.MessageIcon.Critical,
                3000,
            )
            return

    def _do_stop_recording(self) -> None:
        """Actually stop recording (must run on main thread)."""
        if not self._is_recording:
            return

        logger.info("Stopping recording")
        self._is_recording = False
        self._is_processing = True
        self._last_stop_time = time.time()
        self.tray.setIcon(self._make_icon("P"))
        self.tray.setToolTip("STT Keyboard - Processing...")
        self.status_action.setText("Status: Processing...")
        self.indicator.show_processing()
        if config.play_sounds:
            play_stop_sound()

        audio = self.recorder.stop()
        logger.debug(f"Recorded {len(audio)} audio samples")

        def transcribe_worker():
            try:
                if len(audio) > 0:
                    logger.info("Starting transcription")
                    text = self.transcriber.transcribe(audio)
                    logger.info(f"Transcription complete: {len(text)} chars")
                    self._signals.finished.emit(text)
                else:
                    self._signals.finished.emit("")
            except TranscriptionError as e:
                logger.error(f"Transcription error: {e}")
                self._signals.error.emit(str(e))

        thread = threading.Thread(target=transcribe_worker, daemon=True)
        thread.start()

    def _on_transcription_finished(self, text: str) -> None:
        """Handle transcription result (runs on main thread via signal)."""
        if text:
            logger.debug(f"Typing text via {self.typer.method.value}")
            success = self.typer.type_text(text)
            if not success:
                logger.error("Typing failed")
                self.tray.showMessage(
                    "STT Keyboard",
                    "Could not insert transcribed text",
                    QSystemTrayIcon.MessageIcon.Critical,
                    3000,
                )
            else:
                logger.info("Text typed successfully")
        self._finish_processing()

    def _on_transcription_error(self, error_msg: str) -> None:
        """Handle transcription error (runs on main thread via signal)."""
        self.tray.showMessage(
            "STT Keyboard",
            error_msg,
            QSystemTrayIcon.MessageIcon.Critical,
            3000,
        )
        self._finish_processing()

    def _finish_processing(self) -> None:
        """Reset state after processing completes (runs on main thread)."""
        self._is_processing = False
        self.tray.setIcon(self._make_icon("M"))
        self.tray.setToolTip("STT Keyboard - Ready")
        self.status_action.setText("Status: Ready")
        self.indicator.hide()

    def _quit_app(self):
        """Quit the application."""
        self.hotkey.stop()
        self._main_timer.stop()
        self.tray.hide()
        QApplication.quit()

    def run(self):
        """Start the application."""
        self.hotkey.start()
        self.tray.show()
        self.qt_app.exec()
