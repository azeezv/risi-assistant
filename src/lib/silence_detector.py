import numpy as np
from typing import Optional
from time import time


class SilenceDetector:
    """
    Detects when the user stops speaking (silence longer than a threshold).
    Tracks audio RMS energy and emits a callback when silence duration exceeds
    the configured threshold.
    """
    def __init__(self, silence_duration_sec: float = 3.0, rms_threshold: float = 0.01):
        """
        Args:
            silence_duration_sec: Duration of silence (in seconds) to trigger detection.
            rms_threshold: RMS energy below this threshold is considered silence.
        """
        self.silence_duration_sec = silence_duration_sec
        self.rms_threshold = rms_threshold
        
        self.last_sound_time: Optional[float] = None
        self.silence_triggered = False
        self.on_silence_callback = None

    def set_silence_callback(self, callback):
        """Register a callback to be called when silence is detected."""
        self.on_silence_callback = callback

    def process_chunk(self, chunk: np.ndarray) -> bool:
        """
        Process an audio chunk and check if silence threshold has been exceeded.
        
        Args:
            chunk: Audio chunk as numpy array (float32).
        
        Returns:
            True if silence was just detected, False otherwise.
        """
        # Calculate RMS (Root Mean Square) energy
        rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
        
        current_time = time()
        
        # Update last sound time if above threshold
        if rms > self.rms_threshold:
            self.last_sound_time = current_time
            self.silence_triggered = False
            return False
        
        # Check if silence duration exceeded
        if self.last_sound_time is None:
            # No sound has been detected yet
            return False
        
        silence_duration = current_time - self.last_sound_time
        
        if silence_duration >= self.silence_duration_sec and not self.silence_triggered:
            self.silence_triggered = True
            if self.on_silence_callback:
                self.on_silence_callback()
            return True
        
        return False

    def reset(self):
        """Reset the detector state."""
        self.last_sound_time = None
        self.silence_triggered = False
