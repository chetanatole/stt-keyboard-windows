"""Floating visual indicator for recording/processing state.

PyQt6 frameless QWidget with waveform animation.
"""

import math
import time

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import QApplication, QWidget


class FloatingIndicator(QWidget):
    """Siri-style floating indicator with audio-reactive waveform."""

    WIDTH = 120
    HEIGHT = 44

    NUM_BARS = 5
    BAR_WIDTH = 4
    BAR_SPACING = 6
    MIN_BAR_HEIGHT = 4
    MAX_BAR_HEIGHT = 24

    MIN_STATE_CHANGE_INTERVAL = 0.1

    def __init__(self):
        super().__init__()
        self._is_visible = False
        self._is_recording = False
        self._is_processing = False
        self._last_state_change = 0.0
        self._audio_level = 0.0
        self._bar_heights = [self.MIN_BAR_HEIGHT] * self.NUM_BARS
        self._phase = 0.0
        self._processing_phase = 0.0

        # Frameless, always-on-top, tool window (no taskbar), transparent
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._position_window()

    def _position_window(self):
        """Position at bottom-center of primary screen, 80px from bottom."""
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        if screen is None:
            return
        geom = screen.availableGeometry()
        x = geom.x() + (geom.width() - self.WIDTH) // 2
        y = geom.y() + geom.height() - 80 - self.HEIGHT
        self.move(x, y)

    def paintEvent(self, event):
        """Draw the dark pill background and waveform bars."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dark rounded pill background
        bg_path = QPainterPath()
        bg_path.addRoundedRect(
            0.0,
            0.0,
            float(self.WIDTH),
            float(self.HEIGHT),
            self.HEIGHT / 2,
            self.HEIGHT / 2,
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(30, 30, 30, 220))
        painter.drawPath(bg_path)

        # Draw waveform bars
        center_x = self.WIDTH / 2
        center_y = self.HEIGHT / 2
        total_width = (
            self.NUM_BARS * self.BAR_WIDTH + (self.NUM_BARS - 1) * self.BAR_SPACING
        )
        start_x = center_x - total_width / 2

        for i in range(self.NUM_BARS):
            bar_height = self._bar_heights[i]
            bar_x = start_x + i * (self.BAR_WIDTH + self.BAR_SPACING)
            bar_y = center_y - bar_height / 2

            bar_path = QPainterPath()
            bar_path.addRoundedRect(
                bar_x,
                bar_y,
                self.BAR_WIDTH,
                bar_height,
                self.BAR_WIDTH / 2,
                self.BAR_WIDTH / 2,
            )

            if self._is_processing:
                painter.setBrush(QColor(255, 153, 0, 255))
            else:
                painter.setBrush(QColor(255, 255, 255, 242))

            painter.drawPath(bar_path)

        painter.end()

    def show_recording(self):
        """Show recording state with audio-reactive animation."""
        now = time.time()
        if now - self._last_state_change < self.MIN_STATE_CHANGE_INTERVAL:
            return
        self._last_state_change = now

        self._is_recording = True
        self._is_processing = False
        self._is_visible = True
        self.show()

    def show_processing(self):
        """Show processing state with gentle wave animation."""
        now = time.time()
        if now - self._last_state_change < self.MIN_STATE_CHANGE_INTERVAL:
            return
        self._last_state_change = now

        self._is_recording = False
        self._is_processing = True
        self._is_visible = True
        self.show()

    def hide(self):
        """Hide the indicator."""
        self._last_state_change = time.time()
        self._is_visible = False
        self._is_recording = False
        self._is_processing = False
        super().hide()

    def update_audio_level(self, level: float):
        """Update with current audio level (0.0 - 1.0)."""
        if not self._is_recording:
            return
        self._audio_level = level
        self._phase += 0.4

        for i in range(self.NUM_BARS):
            bar_phase = self._phase + i * 0.6
            wave = (math.sin(bar_phase) + 1) / 2

            height_factor = 0.15 + 0.85 * level * (0.4 + 0.6 * wave)
            target_height = (
                self.MIN_BAR_HEIGHT
                + (self.MAX_BAR_HEIGHT - self.MIN_BAR_HEIGHT) * height_factor
            )
            self._bar_heights[i] = self._bar_heights[i] * 0.4 + target_height * 0.6

        self.update()

    def update_animation(self):
        """Update animation. Call this from a timer."""
        if not self._is_visible:
            return

        if self._is_processing:
            self._processing_phase += 0.15

            for i in range(self.NUM_BARS):
                bar_phase = self._processing_phase + i * 0.8
                wave = (math.sin(bar_phase) + 1) / 2
                target_height = (
                    self.MIN_BAR_HEIGHT
                    + (self.MAX_BAR_HEIGHT - self.MIN_BAR_HEIGHT) * 0.3 * wave
                )
                self._bar_heights[i] = self._bar_heights[i] * 0.7 + target_height * 0.3

            self.update()


# Singleton instance
_indicator = None


def get_indicator() -> FloatingIndicator:
    """Get the singleton indicator instance."""
    global _indicator
    if _indicator is None:
        _indicator = FloatingIndicator()
    return _indicator
