from typing import Any

class BaseTTS:
    """
    Abstract interface for Text-to-Speech.
    
    The provider takes a text input and returns audio in a
    standard format (bytes, numpy array, or filepath).
    """
    
    name: str
    
    def speak(self, text: str) -> None:
        """
        Generate sound from the text:
        - stream the audio returned to speakers
        """
        raise NotImplementedError