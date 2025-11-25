from dataclasses import dataclass
from typing import Any, Callable, Dict

@dataclass
class ToolDef:
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    func: Callable[..., Any]

    def to_openai(self):
        """Formats for OpenAI (GPT-4o)"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
                "strict": True # Best practice for GPT-4o
            }
        }

    def to_anthropic(self):
        """Formats for Anthropic (Claude 3.5 Sonnet)"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }

    def to_gemini(self):
        """Formats for Google Gemini"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


TOOL_REGISTRY: Dict[str, ToolDef] = {}

def register_tool(tool: ToolDef):
    TOOL_REGISTRY[tool.name] = tool
