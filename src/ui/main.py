import sys

import numpy as np
import sounddevice as sd

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt6.QtGui import QColor

from src.ui.text_display import TextDisplay
from src.ui.voice_visualizer import VoiceVisualizer

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

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Voice Assistant")
        self.resize(500, 220)
        self.setStyleSheet("background-color: rgb(15, 15, 30);")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # --- VISUALIZER ---
        self.visualizer = VoiceVisualizer(self, bar_count=24)
        self.visualizer.setMinimumHeight(120)

        # --- TEXT LABEL BELOW VISUALIZER ---
        self.text_display = TextDisplay(self)
        self.text_display.append_word("Press 'Start Mic' to begin...Press 'Start Mic' to begin...Press 'Start Mic' to begin...Press 'Start Mic' to begin...Press 'Start Mic' to begin...Press 'Start Mic' to begin...Press 'Start Mic' to begin...")
        
        # --- RECORD BTN ---
        self.toggle_btn = QPushButton("Start Mic")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.toggled.connect(self.toggle_mic)

        layout.addWidget(self.visualizer)
        layout.addWidget(self.text_display)
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
