import random
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QWidget

class VoiceVisualizer(QWidget):
    def __init__(self, parent=None, bar_count=20):
        super().__init__(parent)
        self.bar_count = bar_count
        self.values = [0.0] * bar_count
        self.target_values = [0.0] * bar_count
        self.active = False

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

        self.bar_color = QColor(0, 200, 255)
        self.background = QColor(15, 15, 30)

    def setActive(self, active: bool):
        self.active = active
        if not active:
            self.target_values = [0.0] * self.bar_count

    def update_animation(self):
        if self.active:
            self.target_values = [random.random() for _ in range(self.bar_count)]

        for i in range(self.bar_count):
            current = self.values[i]
            target = self.target_values[i]
            self.values[i] = current + (target - current) * 0.2

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), self.background)

        w = self.width()
        h = self.height()

        bar_width = w / (self.bar_count * 1.5)
        gap = bar_width / 2

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self.bar_color))

        mid_y = h / 2

        for i, value in enumerate(self.values):
            x = i * (bar_width + gap) + gap
            bar_h = value * (h * 0.8)
            y = mid_y - bar_h / 2

            p.drawRoundedRect(
                int(x), int(y),
                int(bar_width), int(bar_h),
                bar_width / 2, bar_width / 2
            )