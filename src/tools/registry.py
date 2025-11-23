from dataclasses import dataclass
from typing import Any, Callable, Dict

@dataclass
class ToolDef:
    name: str
    description: str
    parameters: Dict[str, Any]   # JSON Schema
    func: Callable[..., Any]


TOOL_REGISTRY: Dict[str, ToolDef] = {}

def register_tool(tool: ToolDef):
    TOOL_REGISTRY[tool.name] = tool