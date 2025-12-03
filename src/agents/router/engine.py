import jinja2
import json
from typing import Dict, List, Optional
from src.llm import LLMProvider
from src.tts import TTSProvider
from src.agents.task.engine import TaskAgent
from src.agents.reasoner.engine import ReasoningAgent
import threading

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.router", ""))
template = env.get_template("system.j2")

class RouterAgent:
    def __init__(self, set_content_area_ui):
        self.llm = LLMProvider("gemini")
        self.tts_service = TTSProvider("piperTTS")

        # Instantiate agents
        self.task_agent = TaskAgent()
        self.reasoner = ReasoningAgent()

        self.set_content_area_ui = set_content_area_ui
    
    @property
    def system_prompt(self):
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

            print(f"RouterAgent sending to LLM:\n{full_text}")
            
            response = self.llm.model.inference(
                contents=full_text,
                system_prompt=self.system_prompt
            )

            if not response.text_content:
                self.tts_service.speak("Sorry, I couldn't process your request.")
                return "Could not process the request."

            jsonData = {}

            try:
                jsonData = json.loads(response.text_content)
            except:
                raise Exception("LLM returned a non-json")

            type = jsonData.get("type")

            print(jsonData)

            response_text = jsonData.get("response_text")
            
            if type == "instant_response":
                if response_text:
                    self.tts_service.speak(response_text)
            elif type == "tool_invocation":
                threading.Thread(target=self.tts_service.speak, args=(response_text,), daemon=True).start()

                # Expect either a direct instruction for the task agent, or explicit tool_name/args
                tool_name = jsonData.get("tool_name")
                tool_args = jsonData.get("tool_args")

                if tool_name:
                    # If LLM asked to invoke a named tool, delegate to TaskAgent via its registry/execute if available
                    # For now, TaskAgent.execute_task accepts natural language requests; use that when no explicit args
                    if tool_args and isinstance(tool_args, dict):
                        # Build a natural language instruction if needed
                        instruction = json.dumps({"tool": tool_name, "args": tool_args})
                    else:
                        instruction = jsonData.get("instruction") or jsonData.get("user_request") or full_text
                else:
                    # No specific tool_name — treat as a natural language task for the TaskAgent
                    instruction = jsonData.get("instruction") or jsonData.get("user_request") or full_text

                try:
                    result = self.task_agent.execute_task(instruction)
                    # TaskAgent returns final text describing completion; speak it and return
                    if isinstance(result, str):
                        response_text = result
                        self.tts_service.speak(response_text)
                    else:
                        # If TaskAgent returns structured data, stringify for TTS/display
                        response_text = json.dumps(result)
                        self.tts_service.speak(response_text)
                except Exception as e:
                    response_text = f"Error executing task: {e}"
                    print(response_text)
                    self.tts_service.speak(response_text)

            elif type == "advanced_reasoning":
                threading.Thread(target=self.tts_service.speak, args=(response_text,), daemon=True).start()
                
                reasoning_query = full_text
                try:
                    reasoning_result = self.reasoner.reason(reasoning_query)
                    # reasoning_result expected: { voice_summary, display_content, raw_response }
                    voice = reasoning_result.get("voice_summary") or "I've completed the analysis."
                    display = reasoning_result.get("display_content") or reasoning_result.get("raw_response", "")
                    # Speak concise voice summary and return the display content
                    # self.tts_service.speak(voice)
                    threading.Thread(target=self.tts_service.speak, args=(voice,), daemon=True).start()
                    self.set_content_area_ui(display)
                except Exception as e:
                    response_text = f"Error during advanced reasoning: {e}"
                    print(response_text)
                    self.tts_service.speak(response_text)
            else:
                raise Exception(f"Unknown response type: {type}")
            
            return response_text

        except Exception as e:
            threading.Thread(target=self.tts_service.speak, args=("I’m sorry, could you repeat that?",), daemon=True).start()
            print(f"Error in RouterAgent: {e}")
            return None

        
    
    