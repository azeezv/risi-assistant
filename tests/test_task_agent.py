import sys
import os

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

"""
Example usage of the TaskAgent with ReAct pattern.
"""

from src.agents.task import TaskAgent
from dotenv import load_dotenv


load_dotenv()

def main():
    # Initialize the agent
    agent = TaskAgent()
    
    # Example tasks:
    tasks = [
        "Can you find whats the system time is ?",
        "How many users are there in the system ?",
        "What OS system uses? which version ?",
        "Create a folder called 'my_folder' and verify it exists",
        "Create a file called 'test.txt' in the current directory with the content 'Hello World'",
        "List all Python files in the src directory",
    ]
    
    # Execute a task
    task = tasks[0]
    result = agent.execute_task(task)
    print(f"\nFinal Result:\n{result}")


if __name__ == "__main__":
    main()
