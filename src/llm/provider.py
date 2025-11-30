from typing import Optional, Type, Dict, Any, List
from src.llm.base import BaseProvider
from src.llm.gemini import GeminiProvider


LLM_PROVIDER_MAP: Dict[str, Type[BaseProvider]] = {
    "gemini": GeminiProvider,
}

class LLMProvider():

    def __init__(self, provider: str, model: Optional[str] = None):
        
        ProviderClass = LLM_PROVIDER_MAP[provider]

        self.model = ProviderClass(model=model)

