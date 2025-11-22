import sounddevice as sd
from time import sleep
from scipy.signal import resample_poly

class MicStream:
    def __init__(self, on_stream_callback, sample_rate):

        # Find mic
        device_id, device_info = self.find_input_device()

        self.on_stream_callback = on_stream_callback
        self.device_id = device_id
        self.device_info = device_info
        self.native_rate = int(device_info["default_samplerate"])
        self.taget_sample_rate = sample_rate

        self.print_device()
    
    def print_device(self):
        print("Hardware sample rate:", self.native_rate)
        print("Using microphone:", self.device_info["name"])

    def find_input_device(self):
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                return i, d
        return None, None
    
    def resample_stream(self, indata, frames, time, status):
        # Resample from native_sample_rate → TARGET_RATE
        resampled = resample_poly(indata[:, 0], self.taget_sample_rate, self.native_rate)
        self.on_stream_callback(resampled)
    
    def start_stream(self):
        if self.device_id is None:
            raise RuntimeError("No mic device found.")

        with sd.InputStream(
            device=self.device_id,
            samplerate=self.native_rate,
            channels=1, # Mono
            dtype="float32",
            callback=self.resample_stream,
        ):
            print("Recording... Press Ctrl+C to stop.")
            while True:
                sleep(0.01)