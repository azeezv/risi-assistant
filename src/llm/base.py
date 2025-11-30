from abc import ABC, abstractmethod
from typing import Any, Dict, List,Optional
from src.llm.llm_response import LLMResponse
from src.lib.chat_history import ChatMessage

class BaseProvider(ABC):
    name: str

    def __init__(self, model: Optional[str] = None):
        ...

    @property
    @abstractmethod
    def tools(self) -> List[Dict[str, Any]]:
        ...

    @staticmethod
    @abstractmethod
    def build_content(chats: List[ChatMessage]):
        ...
    
    @abstractmethod
    def inference(
        self, 
        contents: str | List[Dict[str, Any]], 
        system_prompt: str = "",
    ) -> LLMResponse:   
        ...
