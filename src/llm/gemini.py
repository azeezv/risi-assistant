from typing import Any, Dict, List, cast
from google import genai
import os
import json

from src.llm.base import BaseProvider
from src.tools.registry import TOOL_REGISTRY

class GeminiProvider(BaseProvider):
    """
    Uses google-genai SDK.
    Note: Gemini's tool schema is very similar but not identical.
    You may tweak this slightly depending on SDK version.
    """

    def __init__(self, model: str = "models/gemini-2.5-flash"):
        # Prefer explicit env var `GEMINI_MODEL`, then constructor arg, then a
        # reasonable default that exists for most accounts.
        default_model = os.environ.get("GEMINI_MODEL") or model
        self.client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = default_model
        self.name = "gemini"

    @property
    def tools(self) -> List[Dict[str, Any]]:
        # Gemini uses function_declarations with JSON schema
        fns = []
        for t in TOOL_REGISTRY.values():
            fns.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            )
        return [{"function_declarations": fns}]

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Gemini content format: list of turns with parts
        # For simplicity, we just join messages into a single turn prompt.
        user_content = ""
        for m in messages:
            user_content += f"{m['role']}: {m['content']}\n"

        # Single request with the joined prompt
        resp = self.client.models.generate_content(
            model=self.model,
            contents=[{"role": "user", "parts": [{"text": user_content}]}],
            config={"tools": self.tools},
        )

        # SDK returns "candidates". Look for function calls if present.
        # Exact structure may differ slightly; adjust as needed.
        # Defensive checks for response structure
        candidates = getattr(resp, "candidates", []) or []
        if not candidates:
            return ""
        candidate = candidates[0]
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", []) or []

        # Search for a function call
        function_calls = [
            getattr(p, "function_call") for p in parts if getattr(p, "function_call", None) is not None
        ]

        if not function_calls:
            # Plain answer
            texts = [cast(str, p.text) for p in parts if getattr(p, "text", None) is not None]
            return "".join(texts)

        # Handle first function call only (for simplicity)
        fc = function_calls[0]
        tool_name = getattr(fc, "name", None)
        args = dict(getattr(fc, "args", {}) or {})

        if not tool_name:
            tool_result = "Invalid function call: missing tool name."
        else:
            tool_def = TOOL_REGISTRY.get(tool_name)
            if not tool_def:
                tool_result = f"Tool {tool_name} not implemented on server."
            else:
                try:
                    tool_result = tool_def.func(**args)
                except Exception as e:
                    tool_result = f"Error running tool {tool_name}: {e}"

        # Send tool result back to Gemini for final answer
        tool_result_str = json.dumps(tool_result)

        followup_resp = self.client.models.generate_content(
            model=self.model,
            contents=[
                {"role": "user", "parts": [{"text": user_content}]},
                {
                    "role": "model",
                    "parts": [  # echo tool call
                        {
                            "function_call": {
                                "name": tool_name,
                                "args": args,
                            }
                        }
                    ],
                },
                {
                    "role": "tool",
                    "parts": [
                        {
                            "function_response": {
                                "name": tool_name,
                                "response": {"result": tool_result_str},
                            }
                        }
                    ],
                },
            ],
                config={"tools": self.tools},
        )

        followup_candidates = getattr(followup_resp, "candidates", []) or []
        if not followup_candidates:
            return ""
        followup_content = getattr(followup_candidates[0], "content", None)
        followup_parts = getattr(followup_content, "parts", []) or []
        texts = [cast(str, p.text) for p in followup_parts if getattr(p, "text", None) is not None]
        return "".join(texts)