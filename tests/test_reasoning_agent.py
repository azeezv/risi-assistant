import sys
import os
import json

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agents.reasoner import ReasoningAgent


def main():
    # Initialize the agent
    agent = ReasoningAgent()
    
    # Example queries for different problem types
    queries = [
        "Explain how to implement a binary search tree in Python with insert, search, and delete operations.",
        "What is the square root of 256, and how would you calculate it manually?",
        "Analyze the sentiment of this text: 'The product quality was excellent, but the shipping took too long.'",
    ]
    
    # Run reasoning on the first query
    query = queries[0]
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}\n")
    
    result = agent.reason(query)
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    print(f"\n📢 VOICE SUMMARY:\n{result['voice_summary']}")
    print(f"\n📺 DISPLAY CONTENT:\n{result['display_content']}")
    
    # Optionally save result to file
    with open("/tmp/reasoning_result.json", "w") as f:
        json.dump({
            "query": query,
            "voice_summary": result['voice_summary'],
            "display_content": result['display_content']
        }, f, indent=2)
    print("\n✅ Result saved to /tmp/reasoning_result.json")


if __name__ == "__main__":
    main()
