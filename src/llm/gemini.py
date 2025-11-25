from typing import Any, Dict, List, cast, Union
from google.genai import Client as geminiClient, types
import os

from src.llm.base import BaseProvider
from src.tools.registry import TOOL_REGISTRY

class GeminiProvider(BaseProvider):

    def __init__(self, model: str = "models/gemini-2.5-flash"):

        self.name = "gemini"
        default_model = os.environ.get("GEMINI_MODEL") or model
        self.model = default_model
        self.client = geminiClient(api_key=os.environ.get("GEMINI_API_KEY"))

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
    
    def inference(
        self, 
        text: str, 
        system_prompt: str = "", 
        tools: List[Dict[str, Any]] | None = None,
    ) -> Union[str, Dict[str, Any]]:        
    
        config = types.GenerateContentConfig(
            tools=tools,
            safety_settings=[],
            system_instruction=system_prompt,
            response_mime_type="application/json" , 
        )

        # 2. Make the API Call
        resp = self.client.models.generate_content(
            model=self.model,
            contents=[{"role": "user", "parts": [{"text": text}]}],
            config=config,
        )

        # 3. Parse Response (Handle both Tools and Text)
        candidates = getattr(resp, "candidates", []) or []
        if not candidates:
            return ""
        
        candidate = candidates[0]
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", []) or []

        for part in parts:
            # CASE A: Native Function Call (Executor Agent)
            # We convert the special object into a standard Python Dictionary
            fn = getattr(part, "function_call", None)
            if fn:
                return {
                    "tool_name": fn.name,
                    "tool_args": dict(fn.args)
                }
            
            # CASE B: Text / JSON String (Router Agent or Standard Chat)
            txt = getattr(part, "text", None)
            if txt:
                return txt

        return ""