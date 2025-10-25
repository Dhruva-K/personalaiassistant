import sys
import os

src_path = os.path.join(os.path.dirname(__file__), 'langgraph-agent', 'src')
sys.path.insert(0, src_path)

os.chdir(src_path)

from agents.base_agent import BaseAgent
from tools.tool_registry import create_tool_registry
from graph.state_manager import StateManager


def main():
    tool_registry = create_tool_registry()
    agent = BaseAgent(tool_registry)
    state_manager = StateManager(agent, tool_registry)

    print("Personal AI Assistant initialized. Type 'exit' to quit.")

    while True:
        user_input = input("\nHow can I help you? ")

        if user_input.lower() == "exit":
            break

        try:
            response = state_manager.run(user_input)
            print("\nAssistant:", response)
        except Exception as e:
            print(f"\nError: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
