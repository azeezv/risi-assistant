import subprocess

from .registry import ToolDef, register_tool

def run_bash(command: str):
    try:
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"error": str(e)}

register_tool(
    ToolDef(
        name="run_bash",
        description="Execute a safe bash command and return stdout, stderr and returncode",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string"},
            },
            "required": ["command"],
        },
        func=run_bash,
    )
)
