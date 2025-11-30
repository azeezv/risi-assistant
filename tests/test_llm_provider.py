import sys
import os
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.provider import LLMProvider

load_dotenv()

x = LLMProvider(
    provider="gemini",
    model="models/gemini-2.5-flash"
)

contents = x.build_content(
[{
    "role": "user",
    "content": "How  many tools you have acces to? Which is it?"
}]
)

response = x.inference(contents)
print(response)