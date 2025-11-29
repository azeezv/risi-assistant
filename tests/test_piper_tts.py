import sys
import os

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tts import PiperTTS
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        stt = PiperTTS()
        stt.speak("Hello bro Its working")
    except KeyboardInterrupt:
        print("\n👋 Exiting")