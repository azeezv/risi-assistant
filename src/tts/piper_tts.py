from src.tts.base import BaseTTS

from piper import PiperVoice
import sounddevice as sd

voice = PiperVoice.load("/media/abdxzi/New Volume/Work/test/risi/models/en_US-lessac-medium.onnx")

class PiperTTS(BaseTTS):
    def __init__(self):
        self.sample_rate = voice.config.sample_rate
    
    def speak(self, text):

        try:
            audio_chunks = voice.synthesize(text)
            with sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32"
                ) as stream:
                    for chunk in audio_chunks:
                        # Your chunk contains audio_float_array, not audio
                        stream.write(chunk.audio_float_array)
        except Exception as e:
            print(f"error: {e})")
           

# python3 -m piper.download_voices en_US-lessac-medium