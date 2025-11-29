import sys
import os

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tts import DeepGramTTS
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        if not os.environ.get("DEEPGRAM_API_KEY"):
            print("DEEPGRAM_API_KEY not set; set it to run live TTS.")
            raise SystemExit(0)

        stt = DeepGramTTS()
        stt.speak("Hello bro Its working")
    except KeyboardInterrupt:
        print("\n👋 Exiting")