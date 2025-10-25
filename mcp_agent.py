#!/usr/bin/env python3
"""
Personal AI Assistant using Model Context Protocol (MCP)
Integrates multiple MCP servers for email, PDF, calendar, search, and pizza ordering.
Privacy-first design using local LLM for sensitive data.
"""
import os
import asyncio
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


class PersonalAIAssistant:
    def __init__(self):
        self.client = None
        self.agent = None
        self.setup_servers()
    
    def setup_servers(self):
        """Configure MCP servers for all tools."""
        server_path = Path(__file__).parent / "mcp_servers"
        
        self.server_config = {
            "email": {
                "transport": "stdio",
                "command": "python3",
                "args": [str(server_path / "email_server.py")],
            },
            "pdf": {
                "transport": "stdio",
                "command": "python3",
                "args": [str(server_path / "pdf_server.py")],
            },
            "calendar": {
                "transport": "stdio",
                "command": "python3",
                "args": [str(server_path / "calendar_server.py")],
            },
            "search": {
                "transport": "stdio",
                "command": "python3",
                "args": [str(server_path / "search_server.py")],
            },
            "pizza": {
                "transport": "stdio",
                "command": "python3",
                "args": [str(server_path / "pizza_server.py")],
            },
        }
    
    async def initialize(self):
        """Initialize MCP client and agent."""
        print("Initializing Personal AI Assistant with MCP...")
        print("Loading tools from MCP servers...")
        
        self.client = MultiServerMCPClient(self.server_config)
        
        tools = await self.client.get_tools()
        
        print(f"Loaded {len(tools)} tools from MCP servers")
        print("Available capabilities:")
        print("  📧 Email: send_email, draft_email")
        print("  📄 PDF: load_pdf, ask_pdf_question, list_loaded_pdfs")
        print("  📅 Calendar: schedule_meeting, list_upcoming_meetings, ask_meeting_details")
        print("  🔍 Search: search_web, get_webpage_content")
        print("  🍕 Pizza: order_pizza, ask_pizza_preferences, get_menu")
        print()
        
        llm = ChatOllama(
            model="mistral",
            temperature=0.3,
        )
        
        self.agent = create_react_agent(llm, tools)
    
    async def chat(self, message: str) -> str:
        """
        Process a user message and return response.
        
        Args:
            message: User's message/request
        
        Returns:
            Assistant's response
        """
        try:
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=message)]
            })
            
            messages = response.get("messages", [])
            if messages:
                return messages[-1].content
            return "I'm not sure how to respond to that."
        
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    async def run_interactive(self):
        """Run interactive chat loop."""
        await self.initialize()
        
        print("=" * 60)
        print("Personal AI Assistant Ready!")
        print("=" * 60)
        print()
        print("I can help you with:")
        print("  • Writing and sending emails")
        print("  • Reading and answering questions about PDFs")
        print("  • Scheduling meetings on your calendar")
        print("  • Searching the internet for information")
        print("  • Ordering pizzas")
        print()
        print("Privacy Note: PDF processing uses local LLM (Ollama)")
        print("Type 'exit' or 'quit' to end the session")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("You: ")
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                if not user_input.strip():
                    continue
                
                print("\nAssistant: ", end="", flush=True)
                response = await self.chat(user_input)
                print(response)
                print()
            
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {str(e)}\n")


async def main():
    """Main entry point."""
    assistant = PersonalAIAssistant()
    await assistant.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
