import sys
import os
from dotenv import load_dotenv

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.router import RouterAgent

load_dotenv()

def callback(x):
    pass

def main():
    # Initialize the agent
    agent = RouterAgent(callback)
    
    # Example queries for different problem types
    queries = [
        "Is there any docker containers running?",
        "I love you", 
        "Hi there", 
        "Explain how to implement a binary search tree in Python with insert, search, and delete operations.",
        "What is the square root of 256, and how would you calculate it manually?",
        "Analyze the sentiment of this text: 'The product quality was excellent, but the shipping took too long.'",
    ]
    
    # Run reasoning on the first query
    query = queries[0]
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}\n")
    
    result = agent.run(query)
    
    print("\n" + "="*60)
    print("RESULTS:")
    print(result)

if __name__ == "__main__":
    main()
