import sounddevice as sd
from time import sleep
from scipy.signal import resample_poly
from typing import Any, Dict, Optional, Tuple, Callable, cast


class MicStream:
    def __init__(self, on_stream_callback: Callable[[Any], None], sample_rate: int):

        # Find mic
        device_id, device_info = self.find_input_device()

        self.on_stream_callback = on_stream_callback
        self.device_id = device_id
        # normalize device_info to a dict for safe indexing
        self.device_info: Optional[Dict[str, Any]] = cast(Optional[Dict[str, Any]], device_info)

        # Use dict.get to avoid index type errors from stubs that expose different types
        native_sr = None
        if self.device_info is not None:
            native_sr = self.device_info.get("default_samplerate")
        self.native_rate = int(native_sr) if native_sr is not None else sample_rate
        self.target_sample_rate = sample_rate

        self.print_device()

    def print_device(self) -> None:
        print("Hardware sample rate:", self.native_rate)
        if self.device_info is not None:
            print("Using microphone:", self.device_info.get("name"))

    def find_input_device(self) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        devices = sd.query_devices()
        # devices may be a list of dicts; cast for typing
        for i, d in enumerate(devices):
            d_dict = cast(Dict[str, Any], d)
            if d_dict.get("max_input_channels", 0) > 0:
                return i, d_dict
        return None, None

    def resample_stream(self, indata, frames: int, time, status) -> None:
        # Resample from native_sample_rate → TARGET_RATE
        # Use column 0 (mono) safely
        resampled = resample_poly(indata[:, 0], self.target_sample_rate, self.native_rate)
        self.on_stream_callback(resampled)

    def start_stream(self) -> None:
        if self.device_id is None:
            raise RuntimeError("No mic device found.")

        with sd.InputStream(
            device=self.device_id,
            samplerate=self.native_rate,
            channels=1,  # Mono
            dtype="float32",
            callback=self.resample_stream,
        ):
            print("Recording... Press Ctrl+C to stop.")
            while True:
                sleep(0.01)