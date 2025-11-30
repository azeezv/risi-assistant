from src.llm.llm_response import LLMResponse

class BaseProvider:
    name: str

    def inference(
        self, 
        text: str, 
        system_prompt: str = "",
    ) -> LLMResponse:   
        """
        High-level call:
        - takes internal messages [{"role":"user"/"assistant", "content":"..."}]
        - runs model + tools
        - returns final assistant string
        """
        raise NotImplementedError
