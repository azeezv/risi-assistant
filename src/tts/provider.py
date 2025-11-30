from typing import Optional, Type, Dict
from .base import BaseTTS
from .piper_tts import PiperTTS
from .deepgram_tts import DeepGramTTS

TTS_PROVIDER_MAP: Dict[str, Type[BaseTTS]] = {
    "piperTTS": PiperTTS,
    "deepgramTTS": DeepGramTTS
}

class TTSProvider():

    def __init__(self, provider: str):
        
        ProviderClass = TTS_PROVIDER_MAP[provider]

        self.tts = ProviderClass()
    
    def speak(self, text: str) -> None:
        self.tts.speak(text)