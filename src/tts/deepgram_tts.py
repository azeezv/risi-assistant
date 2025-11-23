import asyncio
import os
import numpy as np
from deepgram import DeepgramClient
from src.tts.base import BaseTTS

import sounddevice as sd
import soundfile as sf
from io import BytesIO

class DeepGramTTS(BaseTTS):
    def __init__(self):
        self.client = DeepgramClient(api_key=os.getenv("DEEPGRAM_API_KEY"))

    def tts(self, text):
        chunks = []
        for chunk in self.client.speak.v1.audio.generate(
            text=text,
            model="aura-2-thalia-en",
            encoding="linear16",
            container="wav",
        ):
            chunks.append(chunk)
        return b"".join(chunks)
    
    def speak(self, text):
        
        audio_bytes = self.tts(text)

        try:
            data, samplerate = sf.read(BytesIO(audio_bytes), dtype="float32")
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            print(f"error: {e})")
           