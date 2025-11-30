import os
from typing import Any, Dict, List
from google.genai import Client as geminiClient, types

from src.llm.llm_response import LLMResponse
from src.llm.base import BaseProvider
from src.tools.registry import TOOL_REGISTRY
from src.lib.chat_history import ChatMessage


class GeminiProvider(BaseProvider):
    name = "Gemini"

    def __init__(self, model: str = "models/gemini-2.5-flash"):
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
    
    @staticmethod
    def build_content(chats: List[ChatMessage]):
        contents = []
        
        for chat in chats:
            content = chat["content"]

            parsed_chat = {}

            if isinstance(content, str): # text
                parsed_chat = {"role": chat["role"], "parts": [{"text": content}]}
            if "args" in content: # tool_call
                parsed_chat = {"role": "model", "parts": [{"function_call": content}]}
            if "response" in content: # tool_response
                parsed_chat = {"role": "tool", "parts": [{"function_response": content}]}

            contents.append(parsed_chat)
        
        return contents
    
    def inference(
        self, 
        contents: str | List[Dict[str, Any]], 
        system_prompt: str = "",
        json_mode: bool = False,
        response_schema = None
    ) -> LLMResponse:
        
        _contents: List[Dict[str, Any]] = []

        tools = None if json_mode else self.tools
        config = types.GenerateContentConfig(
            safety_settings=[],
            tools=tools,
            system_instruction=system_prompt,
        )

        if json_mode:
            config.response_mime_type = "application/json"
        if response_schema:
            config.response_schema = response_schema

        if isinstance(contents, str):
            _contents.append({"role": "user", "parts": [{"text": contents }]})
        else:
            _contents = contents

        response = self.client.models.generate_content(
            model=self.model,
            contents=_contents,
            config=config
        )

        candidates = getattr(response, "candidates", []) or []
        if not candidates:
            return LLMResponse(text_content="")
        
        model_candidate = candidates[0]

        text_content = ""
        tool_call = None
        
        content = getattr(model_candidate, "content", None)
        parts = getattr(content, "parts", []) or []

        for part in parts:
            txt = getattr(part, "text", "")
            text_content += txt
            
            if hasattr(part, "function_call") and part.function_call:
                fn_call = part.function_call
                print(fn_call)

                tool_name = getattr(fn_call, "name", None)
                tool_args = getattr(fn_call, "args", None)

                tool_call = {
                    "name": tool_name,
                    "args": tool_args,
                }

        return LLMResponse(text_content=text_content, tool_call=tool_call)