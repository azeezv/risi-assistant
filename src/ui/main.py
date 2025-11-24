import sys
import random
import numpy as np
import sounddevice as sd

from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QPainter, QBrush, QColor
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton


# ===========
# MIC THREAD 
# ===========
class MicThread(QThread):
    volume_signal = pyqtSignal(float)

    def __init__(self, noise_floor=0.02, sensitivity=40):
        super().__init__()
        self.noise_floor = noise_floor
        self.sensitivity = sensitivity
        self.running = True

    def run(self):
        def callback(indata, frames, time, status):
            if not self.running:
                return

            # RMS volume
            vol = float(np.sqrt(np.mean(indata ** 2)))

            if vol < self.noise_floor:
                vol = 0.0

            vol = min(1.0, vol * self.sensitivity)
            self.volume_signal.emit(vol)

        try:
            with sd.InputStream(
                channels=1,
                samplerate=16000,
                blocksize=512,     # lower block = lower latency
                callback=callback
            ):
                while self.running:
                    sd.sleep(10)   # faster loop (low latency)
        except Exception as e:
            print("Audio error:", e)

    def stop(self):
        self.running = False


# ===========
# VISUALIZER 
# ===========
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


# ============
# MAIN WINDOW 
# ============
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Activity Visualizer")
        self.resize(500, 220)

        layout = QVBoxLayout(self)

        self.visualizer = VoiceVisualizer(self, bar_count=24)
        self.visualizer.setMinimumHeight(120)

        self.toggle_btn = QPushButton("Start Mic")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_mic)

        layout.addWidget(self.visualizer)
        layout.addWidget(self.toggle_btn)

        self.mic_thread = None

    def toggle_mic(self, checked):
        if checked:
            self.toggle_btn.setText("Stop Mic")
            self.start_mic()
        else:
            self.toggle_btn.setText("Start Mic")
            self.stop_mic()

    def start_mic(self):
        # create a fresh thread
        self.mic_thread = MicThread(noise_floor=0.0095, sensitivity=40)
        self.mic_thread.volume_signal.connect(self.process_volume)
        self.mic_thread.start()

    def stop_mic(self):
        if self.mic_thread:
            self.mic_thread.running = False
            self.mic_thread.wait()
            self.mic_thread = None

        # stop visualizer
        self.visualizer.setActive(False)

    def process_volume(self, vol):
        # if voice -> animate
        self.visualizer.setActive(vol > 0.01)


# ====
# RUN 
# ====
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
