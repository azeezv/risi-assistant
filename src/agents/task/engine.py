import jinja2
import os

from src.lib import SystemInfo, ChatHistory
from src.llm import LLMProvider
from src.tools import execute_tool

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.task", ""))
template = env.get_template("system.j2")

class TaskAgent:
    """
    Autonomous Task Agent using the ReAct pattern.
    Follows: Analyze → Plan → Act → Verify
    """
    
    def __init__(self):
        self.llm = LLMProvider("gemini")
        self.max_steps = 15
    
    @property
    def system_prompt(self) -> str:
        return template.render(
            user_os= SystemInfo.USER_OS,
            current_dir= SystemInfo.CURRENT_WORKING_DIRECTORY,
        )
    
    def execute_task(self, user_request: str) -> str:
        """
        Execute a task using ReAct loop.
        """
        
        print(f"\n🔹 STARTED TASK: {user_request}\n")
        
        # Initialize chat history with the user request
        chat_history = ChatHistory()

        # add user query to history
        chat_history.add_message("user", user_request)
        
        step = 0
        while step < self.max_steps:
            step += 1
            
            # === ANALYZE ===
            # Call Gemini with tools enabled
            print(f"🤔 Step {step}: Analyzing...")

            contents = self.llm.model.build_content(chat_history.messages)

            print(contents)

            response = self.llm.model.inference(
                contents = contents,
                system_prompt = self.system_prompt
            )

            
            # === PATH 1: AGENT WANTS TO USE A TOOL ===

            if response.tool_call:
                tool = response.tool_call

                tool_name = str(tool.get("name"))
                tool_args = tool.get("args", {})

                # === PLAN ===
                print(f"📋 Plan: Use tool '{tool_name}' with args {tool_args}")

                # === ACT ===
                print(f"⚙️  Step {step}: Executing {tool_name}...")

                try:
                    result_data = execute_tool(tool_name, tool_args)
                except Exception as e:
                    result_data = {"error": str(e)}

                # === VERIFY ===
                print(f"✓ Result: {result_data}")

                chat_history.add_message("model", {
                    "name": tool_name,
                    "args": tool_args
                })

                chat_history.add_message("user", {
                    "name": tool_name,
                    "response": result_data
                })

            elif response.text_content:
                final_text = response.text_content
                print(f"\n✅ TASK COMPLETE:\n{final_text}\n")
                return final_text
            else:
                return "Error: Unexpected response format from model"
        return f"⚠️ Task exceeded max steps ({self.max_steps}). Stopping."
    
