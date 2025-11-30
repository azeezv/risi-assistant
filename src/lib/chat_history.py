from typing import TypedDict, Literal, Dict, List, Union

Role = Literal["user", "model"]

class ToolCall(TypedDict):
    # id: str
    name: str
    args: Dict[str, str]

class ToolResponse(TypedDict):
    # id: str
    name: str
    response: Dict[str, str]

Content = Union[str, ToolCall, ToolResponse]

class ChatMessage(TypedDict):
    role: Role
    content: Content

class ChatHistory():
    def __init__(self):
        self.messages: List[ChatMessage] = []

    def add_message(self, role: Role, content: Content) -> None:
        self.messages.append({
            "role": role,
            "content": content
        })
    
    def get_messages(self) -> List[ChatMessage]:
        return self.messages
    
    def clear(self) -> None:
        self.messages = []

    def __len__(self) -> int:
        return len(self.messages)
    