import sys
import os

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.stt.deepgram_stt import DeepGramSTT
import asyncio
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        stt = DeepGramSTT()
        asyncio.run(stt.start())
    except KeyboardInterrupt:
        print("\n👋 Exiting")