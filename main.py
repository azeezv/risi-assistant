from lib.stt import DeepGram
import asyncio
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        asyncio.run(DeepGram.deepgram_stream())
    except KeyboardInterrupt:
        print("\n👋 Exiting")