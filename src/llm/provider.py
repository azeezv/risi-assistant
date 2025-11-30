from typing import Optional, Type, Dict
from src.llm.base import BaseProvider
from src.llm.gemini import GeminiProvider


LLM_PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "gemini": GeminiProvider,
}

class LLMProvider():

    def __init__(self, provider: str, model: Optional[str] = None):
        
        ProviderClass = LLM_PROVIDER_MAP[provider]
        
        self.llm = ProviderClass(model=model)

    @property
    def tools(self):
        return self.llm.tools

    def build_content(self, chats):
        return self.llm.build_content(chats)

    def inference(self, contents, system_prompt: str = ""):
        return self.llm.inference(contents, system_prompt=system_prompt)
