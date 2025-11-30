from .registry import TOOL_REGISTRY

def execute_tool(tool_name: str, tool_args: dict) -> dict:
    """
    Execute a tool by name.
    """
    
    if TOOL_REGISTRY[tool_name]:
        return TOOL_REGISTRY[tool_name].func(**tool_args)
    else:
        return {"error": f"Tool '{tool_name}' not implemented"}