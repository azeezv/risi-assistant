import jinja2
import json
import os
import platform
from datetime import datetime
from google.genai import Client as geminiClient
from google.genai import types

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
        self.model = model
        self.client = geminiClient(api_key=os.environ.get("GEMINI_API_KEY"))
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with context."""
        return template.render(
            user_os=f"{platform.system()} {platform.release()}",
            user_name=os.getenv("USER", "User"),
            current_date=datetime.now().strftime("%Y-%m-%d"),
            user_query="(provided per request)"
        )
    
    def reason(self, query: str) -> dict:
        """
        Solve a complex problem using deep reasoning.
        
        Args:
            query: The problem or question to solve
        
        Returns:
            Dictionary with:
                - voice_summary: Text for TTS
                - display_content: Markdown for display
                - raw_response: Full response from model
        """
        
        print(f"\n🧠 REASONING: {query}\n")
        
        # Build the prompt with the user query
        prompt = template.render(
            user_os=f"{platform.system()} {platform.release()}",
            user_name=os.getenv("USER", "User"),
            current_date=datetime.now().strftime("%Y-%m-%d"),
            user_query=query
        )
        
        # Call Gemini
        print("🤔 Analyzing problem...")
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=[{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            config=types.GenerateContentConfig(
                safety_settings=[],
            )
        )
        
        # Extract response
        if not response.candidates:
            return {
                "voice_summary": "Error: No response from model",
                "display_content": "Error: No response from model",
                "raw_response": None
            }
        
        model_candidate = response.candidates[0]
        if not model_candidate.content or not model_candidate.content.parts:
            return {
                "voice_summary": "Error: Empty response from model",
                "display_content": "Error: Empty response from model",
                "raw_response": None
            }
        
        response_text = model_candidate.content.parts[0].text
        
        # Parse JSON response
        try:
            # Try to extract JSON from markdown code blocks if needed
            json_text = response_text
            if json_text and "```json" in json_text:
                # Extract JSON from markdown code block
                start = json_text.find("```json") + 7
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()
            elif json_text and "```" in json_text:
                # Try generic code block
                start = json_text.find("```") + 3
                end = json_text.find("```", start)
                if end > start:
                    json_text = json_text[start:end].strip()
            
            if json_text:
                result = json.loads(json_text)
                
                # Validate required fields
                if "voice_summary" not in result:
                    result["voice_summary"] = "Processing complete."
                if "display_content" not in result:
                    result["display_content"] = response_text
                
                result["raw_response"] = response_text
                
                print(f"✅ Reasoning complete\n")
                print(f"📢 Voice Summary:\n{result['voice_summary']}\n")
                print(f"📺 Display Content (first 300 chars):\n{result['display_content'][:300]}...\n")
                
                return result
        except (json.JSONDecodeError, ValueError):
            pass
        
        # If JSON parsing failed, return response as-is
        return {
            "voice_summary": "I've completed the analysis. Please check the display for details.",
            "display_content": response_text,
            "raw_response": response_text
        }
    
    def get_voice_summary(self, result: dict) -> str:
        """Extract voice summary from reasoning result."""
        return result.get("voice_summary", "")
    
    def get_display_content(self, result: dict) -> str:
        """Extract display content from reasoning result."""
        return result.get("display_content", "")
