from typing import Dict, Any

import numpy as np
import sounddevice as sd

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from scipy.signal import resample_poly

class MicWorker(QObject):
    volume_signal = pyqtSignal(float)
    voice_signal = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self, noise_floor=0.02, sensitivity=40):
        super().__init__()
        self.noise_floor = noise_floor
        self.sensitivity = sensitivity
        self.running = False
        self.sample_rate = self.get_sample_rate()

    def get_sample_rate(self):
        default_device = sd.default.device
        if isinstance(default_device, (list, tuple)):
            input_index = default_device[0]
        else:
            input_index = default_device
        try:
            info: Dict[str, Any] = sd.query_devices(input_index, 'input')
            return int(info['default_samplerate'])
        except Exception:
            # Fallback to a common sample rate
            return 16000

    def resample_audio(self, indata, to=16000) -> np.ndarray:
        return resample_poly(indata[:, 0], to, self.sample_rate)

    @pyqtSlot()
    def run(self):
        self.running = True

        def callback(indata: np.ndarray, frames: int, time, status):
            if not self.running:
                return

            vol = float(np.sqrt(np.mean(indata ** 2)))
            if vol < self.noise_floor:
                vol = 0.0
            vol = min(1.0, vol * self.sensitivity)

            resampled = self.resample_audio(indata)

            self.volume_signal.emit(vol)
            self.voice_signal.emit(resampled)

        try:
            # The stream lives entirely inside this thread
            with sd.InputStream(
                channels=1,
                samplerate=self.sample_rate,
                blocksize=512,
                callback=callback
            ):
                while self.running:
                    sd.sleep(10)
        except Exception as e:
            print("Audio error:", e)

        self.finished.emit() 

    @pyqtSlot()
    def stop(self):
        self.running = False


class MicThread():
    def __init__(self, noise_floor=0.02, sensitivity=40):
        self.thread = QThread()
        self.worker = MicWorker(noise_floor=noise_floor, sensitivity=sensitivity)
        self.worker.moveToThread(self.thread)
        
        # signals
        self.thread.started.connect(self.worker.run)
        
        # cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def start(self):
        # start thread
        assert self.thread is not None
        self.thread.start()
    
    def stop(self):
        if self.thread and self.worker:
            if self.thread.isRunning():
                self.worker.stop()
                self.thread.quit()
                self.thread.wait()
