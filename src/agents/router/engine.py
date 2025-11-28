import jinja2
import json
from typing import Any, Dict, List, Optional
from src.llm.gemini import GeminiProvider
from src.tts.deepgram_tts import DeepGramTTS

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.router", ""))
template = env.get_template("system.j2")

class RouterAgent:
    def __init__(self):
        # self.tools = tools
        self.system_prompt = self.__system_prompt()
        self.llm = GeminiProvider()
        self.tts_service = DeepGramTTS()
    
    def __system_prompt(self) -> str:
        return template.render()
    
    def run(self, instruction: str, history: Optional[List[Dict[str, str]]] = None) -> Optional[str]:
        try:
            # Build context from conversation history if provided
            context_text = ""
            if history:
                for msg in history:
                    role = msg.get("role", "").upper()
                    content = msg.get("content", "")
                    context_text += f"{role}: {content}\n"
            
            # Combine history context with current instruction
            full_text = instruction
            if context_text:
                full_text = f"Conversation history:\n{context_text}\nCurrent message: {instruction}"
            
            response = self.llm.inference(
                text=full_text,
                system_prompt=self.system_prompt,
                tools=self.llm.tools,
            )
            jsonData = json.loads(response)
            type = jsonData.get("type")

            print(jsonData)

            response_text = ""
            if type == "instant_response":
                response_text = jsonData.get("response_text", "")
                self.tts_service.speak(response_text)
            elif type == "tool_invocation":
                pass
            elif type == "advanced_reasoning":
                pass
            else:
                raise Exception(f"Unknown response type: {type}")
            
            return response_text

        except Exception as e:
            print(f"Error in RouterAgent: {e}")
            return None

        
    
    