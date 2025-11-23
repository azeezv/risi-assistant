from typing import Dict, List

class BaseProvider:
    name: str

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        High-level call:
        - takes internal messages [{"role":"user"/"assistant", "content":"..."}]
        - runs model + tools
        - returns final assistant string
        """
        raise NotImplementedError
