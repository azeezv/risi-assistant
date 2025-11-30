from typing import List, Dict
from collections import deque

class ConversationHistory:
    """
    Manages conversation history with a maximum of N exchanges.
    Each exchange contains a user message and an assistant response.
    """
    def __init__(self, max_exchanges: int = 20):
        self.max_exchanges = max_exchanges
        self.history: deque = deque(maxlen=max_exchanges * 2)  # 2 for user + assistant
    
    def add_user_message(self, message: str) -> None:
        self.history.append({
            "role": "user",
            "content": message
        })
    
    def add_assistant_message(self, message: str) -> None:
        self.history.append({
            "role": "model",
            "content": message
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        return list(self.history)
    
    def get_formatted_context(self) -> str:
        if not self.history:
            return ""
        
        lines = []
        for msg in self.history:
            role = msg["role"].upper()
            content = msg["content"]
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        self.history.clear()
    
    def __len__(self) -> int:
        return len(self.history)
