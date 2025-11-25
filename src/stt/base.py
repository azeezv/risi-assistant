from PyQt6.QtCore import QObject, QThread, pyqtSignal
import numpy as np

class BaseSTT(QObject):
    """
    Abstract QObject interface for a streaming Speech-to-Text worker.
    """
        
    # --- OUTPUT SIGNALS ---
    trascript_signal = pyqtSignal(str) # new transcript text available
    finished = pyqtSignal()  #  run() method has completed

    # -- INPUT SIGNALS ---


    def __init__(self):
        super().__init__()

    def process_audio_chunk(self, audio_chunk: np.ndarray):
        """Public slot for the worker to receive streaming audio data."""
        raise NotImplementedError
    
    def stop(self):
        """Public slot to command the worker to stop processing."""
        raise NotImplementedError

    def start(self):
        """The main entry point to be called when the thread starts."""
        raise NotImplementedError
    
    def on_transcript(self):
        """Handles incoming transcript messages from STT  service."""
        raise NotImplementedError


class STTThread:
    """
    A generic controller that manages running any BaseSTT worker in a QThread.
    """
    def __init__(self, worker: BaseSTT):
        if not isinstance(worker, BaseSTT):
            raise TypeError("The provided worker must be a subclass of BaseSTT.")

        self.thread = QThread()
        self.worker = worker
        self.worker.moveToThread(self.thread)

        # --- Connect Lifecycle Signals ---
        self.thread.started.connect(self.worker.start)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def start(self):
        """Starts the worker thread."""
        self.thread.start()

    def stop(self):
        """Stops the worker thread gracefully."""
        if self.thread.isRunning():
            self.worker.stop()
            self.thread.wait()