import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.router.engine import system_prompt_str

print("Generated System Prompt:")
print(system_prompt_str)