import sys
import os

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm import GeminiProvider
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    try:
        # Require GEMINI_API_KEY to actually call the remote API. If missing,
        # print an informative message and exit so this script can be run
        # safely in CI/dev environments.
        if not os.environ.get("GEMINI_API_KEY"):
            print("GEMINI_API_KEY not set; set it to run a live Gemini test.")
            raise SystemExit(0)

        llm = GeminiProvider()

        # Quick test message
        messages = [{"role": "user", "content": "Hello Gemini — please reply briefly which tools are  availble to you."}]
        try:
            resp = llm.inference("Hello, Are you there?", system_prompt="You are a helpful assistant.")
            print("Gemini response:\n", resp)
        except Exception as e:
            print("Error running GeminiProvider.chat:", e)
    except KeyboardInterrupt:
        print("\n👋 Exiting")