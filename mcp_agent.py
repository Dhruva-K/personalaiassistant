#!/usr/bin/env python3
"""
Personal AI Assistant using Model Context Protocol (MCP)
Integrates multiple MCP servers for email, PDF, calendar, search, and pizza ordering.
Uses Hugging Face Inference API for language model capabilities.
Features memory and advanced reasoning capabilities.
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace


SYSTEM_PROMPT = """You are a highly capable Personal AI Assistant with access to multiple tools to help users with their daily tasks. Your primary goal is to be helpful, efficient, and proactive.

## Your Capabilities:
1. **Email Management** (send_email, draft_email)
   - Write professional, clear emails
   - Send emails on behalf of the user
   - Draft emails for user review

2. **PDF Document Processing** (load_pdf, ask_pdf_question, list_loaded_pdfs)
   - Load and read multiple PDF files
   - Answer questions about PDF content
   - Extract and summarize information from PDFs

3. **Calendar Management** (schedule_meeting, list_upcoming_meetings, ask_meeting_details)
   - Schedule meetings with proper time slots
   - List and manage upcoming meetings
   - Provide details about scheduled events

4. **Web Search** (search_web, get_webpage_content)
   - Search the internet for real-time information
   - Fetch and analyze webpage content
   - Provide up-to-date information on current events

5. **Pizza Ordering** (order_pizza, ask_pizza_preferences, get_menu)
   - Take pizza orders with customization
   - Remember user preferences
   - Provide menu information and recommendations

## Core Principles:

### CRITICAL: Always Use Tools - Never Fake Results
- You MUST actually call the tools you have available
- NEVER generate placeholder text like "[weather condition]" or "[temperature]"
- NEVER pretend you called a tool when you didn't
- If you need information, USE THE TOOL to get it
- Always wait for actual tool results before responding

### Reasoning and Tool Selection
- **Think before acting**: Analyze each request to determine which tool(s) are needed
- **Use the right tool**: Select the most appropriate tool for each task
- **Actually call the tool**: Don't describe what you would do - DO IT
- **Chain tools logically**: If a task requires multiple steps, use tools in sequence
- **Handle dependencies**: If information is needed before taking action, gather it first

### Asking Questions
You MUST ask clarifying questions when:
- **Private information is needed**: email addresses, phone numbers, passwords, payment details
- **Details are ambiguous**: meeting times, recipient names, pizza toppings, search queries need specifics
- **Confirmation is required**: before sending emails, ordering food, or scheduling important meetings
- **Multiple options exist**: when user's intent could be interpreted in different ways
- **You're uncertain**: it's better to ask than to make wrong assumptions

### Communication Style
- Be conversational, friendly, and professional
- Explain what you're doing ("Let me search for that...")
- Show actual results from tools
- Confirm actions before executing them (especially for emails, orders, and calendar events)
- Provide context and reasoning for your decisions
- If a tool fails, explain why and suggest alternatives

### Error Handling
- If a tool fails, explain the error clearly
- Suggest alternative approaches
- Ask for additional information if needed to retry
- Never pretend an action succeeded if it failed

### Privacy and Security
- Never assume private information (emails, phone numbers, addresses)
- Always ask before sending emails or placing orders
- Respect user privacy and data security
- Confirm sensitive actions explicitly

## Example Tool Usage:

**Weather Question**: "What's the weather today?"
1. Think: "I need current weather information"
2. Action: Call search_web("weather today")
3. Wait for results
4. Respond with ACTUAL data from the search results

**Email Request**: "Send an email to John about the meeting"
- ASK: "I'd be happy to send an email to John. Could you provide his email address and what you'd like to say about the meeting?"

**PDF Question**: "What does the contract say about payment?"
- FIRST: Call list_loaded_pdfs to check if PDF is loaded
- IF NOT: Ask user which PDF file to load
- IF YES: Call ask_pdf_question with the query
- RESPOND: Provide clear answer with relevant excerpts

**Pizza Order**: "Order me a pizza"
- ASK: "I can help you order a pizza! What size would you like, and what toppings? Also, should I use your saved preferences or would you like something different?"

Remember: You're an assistant that takes REAL ACTION. Always call tools and use their actual results. Never fake or simulate responses."""


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
        """Initialize MCP client and agent with memory."""
        print("Initializing Personal AI Assistant with MCP...")
        print("Loading tools from MCP servers...")
        
        self.client = MultiServerMCPClient(self.server_config)
        
        tools = await self.client.get_tools()
        
        print(f"✓ Loaded {len(tools)} tools from MCP servers")
        print("\nAvailable tools:")
        for tool in tools:
            print(f"  • {tool.name}: {tool.description}")
        print()
        
        # Create the Hugging Face LLM
        llm = self._create_llm()

        # Create agent with system prompt and memory
        # The agent automatically maintains conversation history through message state
        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=SYSTEM_PROMPT
        )
        
        print("✓ Agent initialized with memory and reasoning capabilities")
        print()

    def _create_llm(self):
        """Create a HuggingFace LLM instance based on environment variables."""
        load_dotenv()
        
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "HUGGINGFACEHUB_API_TOKEN not set. Please set this environment variable with your Hugging Face API token."
            )

        # Use a model known to work well with tool calling
        # Options: mistralai/Mixtral-8x7B-Instruct-v0.1, meta-llama/Meta-Llama-3-8B-Instruct
        model = os.getenv("HUGGINGFACEHUB_MODEL", "mistralai/Mixtral-8x7B-Instruct-v0.1")
        temp = float(os.getenv("LLM_TEMPERATURE", "0.1"))  # Lower temp for more reliable tool calling
        
        print(f"Using Hugging Face Hub LLM:")
        print(f"  Model: {model}")
        print(f"  Temperature: {temp}")

        endpoint = HuggingFaceEndpoint(
            repo_id=model,
            huggingfacehub_api_token=hf_token,
            temperature=temp,
            max_new_tokens=2048,
            top_p=0.95,
        )
        
        llm = ChatHuggingFace(llm=endpoint, verbose=True)
        return llm
    
    async def chat(self, message: str) -> str:
        """
        Process a user message and return response.
        The agent maintains conversation history automatically.
        
        Args:
            message: User's message/request
        
        Returns:
            Assistant's response
        """
        try:
            print(f"\n[DEBUG] Processing message: {message}")
            
            # The agent's state maintains message history automatically
            # Each invocation adds to the conversation context
            response = await self.agent.ainvoke({
                "messages": [HumanMessage(content=message)]
            })
            
            print(f"[DEBUG] Agent response keys: {response.keys()}")
            print(f"[DEBUG] Number of messages: {len(response.get('messages', []))}")
            
            messages = response.get("messages", [])
            if messages:
                # Print all messages for debugging
                print("\n[DEBUG] Message sequence:")
                for i, msg in enumerate(messages):
                    msg_type = type(msg).__name__
                    content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else str(msg)[:100]
                    print(f"  {i}. {msg_type}: {content_preview}...")
                
                # Return the last message (agent's response)
                final_response = messages[-1].content
                print(f"\n[DEBUG] Final response: {final_response[:200]}...\n")
                return final_response
            
            return "I'm not sure how to respond to that."
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"\n[ERROR] Exception occurred:\n{error_details}")
            return f"Error processing request: {str(e)}\n\nPlease try rephrasing your request or ask me to try again."
    
    async def run_interactive(self):
        """Run interactive chat loop with memory."""
        await self.initialize()
        
        print("=" * 60)
        print("🤖 Personal AI Assistant Ready!")
        print("=" * 60)
        print()
        print("I can help you with:")
        print("  • Writing and sending emails")
        print("  • Reading and answering questions about PDFs")
        print("  • Scheduling meetings on your calendar")
        print("  • Searching the internet for information")
        print("  • Ordering pizzas")
        print()
        print("💡 I will ask you questions when I need more information")
        print("💬 I remember our conversation context")
        print("🧠 I reason about tasks before selecting tools")
        print()
        print("Type 'exit' or 'quit' to end the session")
        print("Type 'help' to see example commands")
        print("Type 'debug on' to enable detailed logging")
        print("Type 'debug off' to disable detailed logging")
        print("=" * 60)
        print()
        
        debug_mode = False
        
        while True:
            try:
                user_input = input("You: ")
                
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye! Have a great day! 👋")
                    break
                
                if user_input.lower() == 'debug on':
                    debug_mode = True
                    print("✓ Debug mode enabled\n")
                    continue
                
                if user_input.lower() == 'debug off':
                    debug_mode = False
                    print("✓ Debug mode disabled\n")
                    continue
                
                if user_input.lower() == 'help':
                    self._print_help()
                    continue
                
                if not user_input.strip():
                    continue
                
                print("\n🤖 Assistant: ", end="", flush=True)
                response = await self.chat(user_input)
                
                # Clean up debug output from response if not in debug mode
                if not debug_mode and "[DEBUG]" in response:
                    response = "\n".join(line for line in response.split("\n") if "[DEBUG]" not in line)
                
                print(response)
                print()
            
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    def _print_help(self):
        """Print example commands."""
        print("\n" + "=" * 60)
        print("Example Commands:")
        print("=" * 60)
        print("\n📧 Email:")
        print("  • Send an email to john@example.com about the project update")
        print("  • Draft an email to my team")
        print("\n📄 PDF:")
        print("  • Load the contract.pdf file")
        print("  • What does the document say about payment terms?")
        print("  • List all loaded PDFs")
        print("\n📅 Calendar:")
        print("  • Schedule a meeting with Sarah on Friday at 2pm")
        print("  • What meetings do I have coming up?")
        print("  • Tell me about my meeting with the sales team")
        print("\n🔍 Search:")
        print("  • What's the weather like today?")
        print("  • Search for the latest AI news")
        print("  • Find information about Python decorators")
        print("\n🍕 Pizza:")
        print("  • Order me a large pepperoni pizza")
        print("  • What's on the menu?")
        print("  • Order my usual pizza")
        print("\n" + "=" * 60 + "\n")


async def main():
    """Main entry point."""
    assistant = PersonalAIAssistant()
    await assistant.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())