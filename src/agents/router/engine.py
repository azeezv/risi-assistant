import jinja2
import json
# from typing import Any, Dict, List
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
    
    def run(self, instruction: str) -> None:
        try:
            response = self.llm.inference(
                text=instruction,
                system_prompt=self.system_prompt,
                tools=self.llm.tools,
            )
            jsonData = json.loads(response)
            type = jsonData.get("type")

            if type == "instant_response":
                self.tts_service.speak(jsonData.get("response_text", ""))
            elif type == "tool_invocation":
                pass
            elif type == "advanced_reasoning":
                pass
            else:
                raise Exception(f"Unknown response type: {type}")

        except Exception as e:
            print(f"Error in RouterAgent: {e}")

        
    
    