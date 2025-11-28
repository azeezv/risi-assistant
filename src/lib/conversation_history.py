from typing import List, Dict, Any
from collections import deque


class ConversationHistory:
    """
    Manages conversation history with a maximum of N exchanges.
    Each exchange contains a user message and an assistant response.
    """
    def __init__(self, max_exchanges: int = 20):
        """
        Args:
            max_exchanges: Maximum number of user/assistant pairs to keep.
        """
        self.max_exchanges = max_exchanges
        self.history: deque = deque(maxlen=max_exchanges * 2)  # 2 for user + assistant
    
    def add_user_message(self, message: str) -> None:
        """Add a user message to history."""
        self.history.append({
            "role": "user",
            "content": message
        })
    
    def add_assistant_message(self, message: str) -> None:
        """Add an assistant response to history."""
        self.history.append({
            "role": "assistant",
            "content": message
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Return conversation history as a list of messages for LLM.
        Format: [{"role": "user|assistant", "content": "..."}, ...]
        """
        return list(self.history)
    
    def get_formatted_context(self) -> str:
        """
        Return formatted conversation history as a string for context.
        Useful for passing to LLM in system prompt or as context.
        """
        if not self.history:
            return ""
        
        lines = []
        for msg in self.history:
            role = msg["role"].upper()
            content = msg["content"]
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def clear(self) -> None:
        """Clear all history."""
        self.history.clear()
    
    def __len__(self) -> int:
        """Return number of messages in history."""
        return len(self.history)
