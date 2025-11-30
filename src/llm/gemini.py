import os
from typing import Any, Dict, List, cast
from google.genai import Client as geminiClient, types

from src.llm.llm_response import LLMResponse
from src.llm.base import BaseProvider
from src.tools.registry import TOOL_REGISTRY
from src.lib.chat_history import ChatMessage


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
    
    def parse_chat(self, chat: ChatMessage):
        content = chat["content"]

        if isinstance(content, str): # text
            return {"role": chat["role"], "parts": [{"text": content}]}
        if "args" in content: # tool_call
            return {"role": "model", "parts": [{"function_call": content}]}
        if "response" in content: # tool_response
            return {"role": "tool", "parts": [{"function_response": content}]}

    def build_content(self, chat_history: List[ChatMessage], query: str):
        content = []
        for chat in chat_history:
            content.append(
                self.parse_chat(chat)
            )
        content.append(
            {
                "role": "user", 
                "parts": [
                    {"text": query}
                ]
            }
        )

        return content
    
    def inference(
        self, 
        text: str, 
        system_prompt: str = "",
        chat_history: List[ChatMessage] = []
    ) -> LLMResponse:
        response = self.client.models.generate_content(
            model=self.model,
            contents=self.build_content(chat_history, text),
            config=types.GenerateContentConfig(
                safety_settings=[],
                tools=self.tools,
                system_instruction=system_prompt,
            )
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
            text_content = txt
            
            if hasattr(part, "function_call") and part.function_call:
                fn_call = part.function_call

                tool_name = getattr(fn_call, "name", None)
                tool_args = getattr(fn_call, "args", None)

                tool_call = {
                    "name": tool_name,
                    "args": tool_args,
                }

        return LLMResponse(text_content=text_content, tool_call=tool_call)