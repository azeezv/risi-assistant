import jinja2
import os
import platform
from google.genai import Client as geminiClient
from google.genai import types

from src.tools.registry import TOOL_REGISTRY
from src.tools.run_bash import run_bash

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.task", ""))
template = env.get_template("system.j2")


class TaskAgent:
    """
    Autonomous Task Agent using the ReAct pattern.
    Follows: Analyze → Plan → Act → Verify
    
    Flow:
    1. Agent analyzes the task and chat history
    2. Agent calls a tool (run_bash, etc.) or returns final answer
    3. Tool result is fed back to the agent
    4. Repeat until agent says the task is complete
    """
    
    def __init__(self, model: str = "models/gemini-2.5-flash"):
        self.model = model
        self.client = geminiClient(api_key=os.environ.get("GEMINI_API_KEY"))
        self.max_steps = 15
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with OS and directory context."""
        return template.render(
            user_os=f"{platform.system()} {platform.release()}",
            current_dir=os.getcwd(),
            user_request="(provided per task)"
        )
    
    @property
    def tools(self):
        """Return tools in Gemini format."""
        fns = []
        for t in TOOL_REGISTRY.values():
            fns.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            })
        return [{"function_declarations": fns}]
    
    def execute_task(self, user_request: str) -> str:
        """
        Execute a task using ReAct loop.
        
        Args:
            user_request: The task to execute
        
        Returns:
            Final response from the agent
        """
        
        print(f"\n🔹 STARTED TASK: {user_request}\n")
        
        # Initialize chat history with the user request
        chat_history = []
        
        step = 0
        while step < self.max_steps:
            step += 1
            
            # === ANALYZE ===
            # Call Gemini with tools enabled
            print(f"🤔 Step {step}: Analyzing...")
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=self._build_contents(user_request, chat_history),
                config=types.GenerateContentConfig(
                    tools=self.tools,
                    safety_settings=[],
                    system_instruction=self.system_prompt,
                    # Don't use response_mime_type with function calling
                )
            )
            
            # Extract the model's response
            if not response.candidates:
                return "Error: No response from model"
            
            model_candidate = response.candidates[0]
            if not model_candidate.content or not model_candidate.content.parts:
                return "Error: Empty response from model"
            
            model_part = model_candidate.content.parts[0]
            
            # === PATH 1: AGENT WANTS TO USE A TOOL ===
            if hasattr(model_part, "function_call") and model_part.function_call:
                fn_call = model_part.function_call
                
                # Safely extract tool_name
                tool_name = getattr(fn_call, "name", None)
                if not isinstance(tool_name, str) or not tool_name:
                    return "Error: Invalid tool name from model"
                
                # Convert protobuf args to dict
                tool_args = self._protobuf_to_dict(getattr(fn_call, "args", None))
                
                # === PLAN ===
                print(f"📋 Plan: Use tool '{tool_name}' with args {tool_args}")
                
                # === ACT ===
                print(f"⚙️  Step {step}: Executing {tool_name}...")
                try:
                    result_data = self._execute_tool(tool_name, tool_args)
                except Exception as e:
                    result_data = {"error": str(e)}
                
                # === VERIFY ===
                print(f"✓ Result: {result_data}")
                
                # Append model's response with function call to history
                # Keep the original model_part object for proper API formatting
                chat_history.append({
                    "role": "model",
                    "parts": [model_part]
                })
                
                # Append tool result as function response
                # Format: [role:user, parts:[function_response]]
                chat_history.append({
                    "role": "user",
                    "parts": [{
                        "function_response": {
                            "name": tool_name,
                            "response": result_data
                        }
                    }]
                })
                
                # Loop continues...
            
            # === PATH 2: AGENT IS DONE (TEXT RESPONSE) ===
            elif hasattr(model_part, "text") and model_part.text:
                final_text = model_part.text
                print(f"\n✅ TASK COMPLETE:\n{final_text}\n")
                return final_text
            
            else:
                return "Error: Unexpected response format from model"
        
        return f"⚠️ Task exceeded max steps ({self.max_steps}). Stopping."
    
    def _build_contents(self, user_request: str, chat_history: list) -> list:
        """Build the contents list for the API call."""
        contents = []
        
        # First turn: include user request
        if not chat_history:
            contents.append({
                "role": "user",
                "parts": [{"text": user_request}]
            })
        else:
            # Subsequent turns: add the initial user request as context
            # Then add the chat history
            contents.append({
                "role": "user",
                "parts": [{"text": user_request}]
            })
            # Add all the chat history items
            contents.extend(chat_history)
        
        return contents
    
    def _protobuf_to_dict(self, protobuf_obj) -> dict:
        """
        Convert a protobuf message to a dict safely.
        Handles Gemini API's protobuf message format.
        
        Args:
            protobuf_obj: A protobuf message object or None or dict
        
        Returns:
            Dictionary representation
        """
        if protobuf_obj is None:
            return {}
        
        # If it's already a dict, just return it
        if isinstance(protobuf_obj, dict):
            return protobuf_obj
        
        try:
            result = {}
            
            # Try to convert to dict if it has that method (protobuf v3+)
            if hasattr(protobuf_obj, 'to_dict') and callable(getattr(protobuf_obj, 'to_dict')):
                try:
                    return protobuf_obj.to_dict()
                except Exception:
                    pass
            
            # Try __dict__
            if hasattr(protobuf_obj, '__dict__'):
                for key, value in protobuf_obj.__dict__.items():
                    if not key.startswith('_') and value is not None:
                        result[key] = value
            
            if result:
                return result
            
            # Try to access ListValue structure (common in Gemini protobuf)
            if hasattr(protobuf_obj, 'fields'):
                fields = getattr(protobuf_obj, 'fields', None)
                if fields and hasattr(fields, 'items'):
                    for key, val in fields.items():
                        # Try to extract value from protobuf Value type
                        if hasattr(val, 'string_value'):
                            result[key] = val.string_value
                        elif hasattr(val, 'number_value'):
                            result[key] = val.number_value
                        elif hasattr(val, 'bool_value'):
                            result[key] = val.bool_value
                        else:
                            result[key] = val
                    if result:
                        return result
            
            # Fallback: iterate attributes using dir()
            for attr_name in dir(protobuf_obj):
                if attr_name.startswith('_'):
                    continue
                try:
                    attr_value = getattr(protobuf_obj, attr_name)
                    # Skip methods and built-in attributes
                    if callable(attr_value) or attr_value is None:
                        continue
                    # Skip descriptor/property objects
                    if isinstance(attr_value, (property, type)):
                        continue
                    result[attr_name] = attr_value
                except Exception:
                    pass
            
            return result
        except Exception:
            return {}
    
    def _execute_tool(self, tool_name: str, tool_args: dict) -> dict:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool
        
        Returns:
            Result dictionary
        """
        if tool_name == "run_bash":
            return run_bash(**tool_args)
        else:
            return {"error": f"Tool '{tool_name}' not implemented"}
