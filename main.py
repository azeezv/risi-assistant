from lib.stt.DeepGram import DeepGramSTT
import asyncio
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        stt = DeepGramSTT()
        asyncio.run(stt.start())
    except KeyboardInterrupt:
        print("\n👋 Exiting")