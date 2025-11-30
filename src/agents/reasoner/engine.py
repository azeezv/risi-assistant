import jinja2
import json

from src.lib.system_info import SystemInfo
from src.llm import GeminiProvider

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.reasoner", ""))
template = env.get_template("system.j2")


class ReasoningAgent:
    """
    Deep Reasoning Agent for solving complex problems.
    Handles: Coding, Math, Analysis, Creative Writing
    
    Produces dual outputs:
    1. voice_summary: Concise summary for TTS
    2. display_content: Detailed markdown for display
    """
    
    def __init__(self, model: str = "models/gemini-2.5-flash"):
        self.llm = GeminiProvider(model=model)

    @property
    def system_prompt(self) -> str:
        return template.render(
            user_os = SystemInfo.USER_OS,
            current_date = SystemInfo.CURRENT_DATE,
            current_dir = SystemInfo.CURRENT_WORKING_DIRECTORY,
        )
    
    def reason(self, query: str) -> dict:        
        print(f"\n🧠 REASONING: {query}\n")
    
        # Call Gemini
        print("🤔 Analyzing problem...")
        
        response = self.llm.inference(
            contents=query,
            system_prompt=self.system_prompt
        )
        
        if not response.text_content:
            return {
                "voice_summary": "Some thing happend i cant find the details.",
                "display_content": ""
            }
        
        jsonData = json.loads(response.text_content)
        
        voice_summary = jsonData.get("voice_summary", "Some thing happend i cant find the details.")
        display_content = jsonData.get("display_content", "")
        
        return {
            "voice_summary": voice_summary,
            "display_content": display_content
        }
