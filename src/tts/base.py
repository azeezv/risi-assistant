from typing import Any

class BaseTTS:
    """
    Abstract interface for Text-to-Speech.
    
    The provider takes a text input and returns audio in a
    standard format (bytes, numpy array, or filepath).
    """
    
    name: str

    def tts(self, text: str) -> Any:
        """
        High-level TTS method:
        - takes a plain text string
        - generates speech via underlying model
        - returns audio (numpy array, bytes, or file path)
        """
        raise NotImplementedError
    
    def speak(self, text: str) -> Any:
        """
        Generate sound from the text:
        - stream the audio returned to speakers
        """
        raise NotImplementedError