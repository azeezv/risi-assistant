from typing import Dict, Any

import numpy as np
import sounddevice as sd

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from scipy.signal import resample_poly
from src.lib.silence_detector import SilenceDetector

class MicWorker(QObject):
    volume_signal = pyqtSignal(float)
    voice_signal = pyqtSignal(np.ndarray)
    silence_signal = pyqtSignal()  # Emitted when silence > threshold
    finished = pyqtSignal()

    def __init__(self, noise_floor=0.02, sensitivity=40, silence_duration_sec=2.0):
        super().__init__()
        self.noise_floor = noise_floor
        self.sensitivity = sensitivity
        self.silence_duration_sec = silence_duration_sec
        self.running = False
        self.sample_rate = self.get_sample_rate()
        self.silence_detector = SilenceDetector(
            silence_duration_sec=silence_duration_sec,
            rms_threshold=noise_floor
        )
        self.silence_detector.set_silence_callback(self._on_silence)

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

    def _on_silence(self):
        """Called by SilenceDetector when silence is detected. Emit Qt signal."""
        self.silence_signal.emit()

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

            # Check for silence (for turn-taking/instruction boundaries)
            self.silence_detector.process_chunk(resampled)

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
    def __init__(self, noise_floor=0.02, sensitivity=40, silence_duration_sec=3.0):
        self.thread = QThread()
        self.worker = MicWorker(noise_floor=noise_floor, sensitivity=sensitivity, silence_duration_sec=silence_duration_sec)
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
