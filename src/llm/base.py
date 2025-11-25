from typing import Dict, List, Union, Any

class BaseProvider:
    name: str

    def inference(
        self, 
        text: str, 
        system_prompt: str = "", 
        tools: List[Dict[str, Any]] | None = None,
    ) -> Union[str, Dict[str, Any]]:   
        """
        High-level call:
        - takes internal messages [{"role":"user"/"assistant", "content":"..."}]
        - runs model + tools
        - returns final assistant string
        """
        raise NotImplementedError
