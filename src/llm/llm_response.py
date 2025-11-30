from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class LLMResponse:
    # If the model wants to talk
    text_content: Optional[str] = None
    
    # If the model wants to act
    # format: {"name": "run_bash", "args": {"command": "ls"}}
    tool_call: Optional[Dict[str, Any]] = None