from langchain.chat_models import ChatOllama
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any, List


class BaseAgent:
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry
        # Initialize Ollama for private data processing
        self.llm = ChatOllama(
            model="mistral",  # You can change this to other models available in Ollama
            temperature=0.1,
            streaming=True,
        )

        # Define the base prompt template for the agent
        self.base_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a personal AI assistant that can help with various tasks:
            1. Writing and sending emails
            2. Reading and analyzing PDF files
            3. Scheduling meetings
            4. Searching the internet
            5. Ordering pizzas
            
            You must:
            - Always protect private information
            - Ask for clarification when uncertain
            - Use local processing for private data
            - Be clear about your capabilities and limitations""",
                ),
                ("human", "{input}"),
                ("assistant", "{agent_scratchpad}"),
            ]
        )

    def decide_tool(self, request: Dict[str, Any]) -> Any:
        # Format the prompt with user request
        messages = self.base_prompt.format_messages(
            input=request.get("input", ""), agent_scratchpad=""
        )

        # Get tool selection from LLM
        response = self.llm.invoke(messages)

        # Parse response to determine appropriate tool
        tool_id = self.parse_tool_selection(response.content)
        tool = self.tool_registry.get_tool(tool_id)
        return tool

    def parse_tool_selection(self, llm_response: str) -> str:
        """Parse LLM response to determine which tool to use"""
        # This is a basic implementation - you might want to make it more sophisticated
        tool_keywords = {
            "email": "email_tool",
            "pdf": "pdf_tool",
            "schedule": "calendar_tool",
            "meeting": "calendar_tool",
            "search": "search_tool",
            "pizza": "order_tool",
            "order": "order_tool",
        }

        llm_response = llm_response.lower()
        for keyword, tool_id in tool_keywords.items():
            if keyword in llm_response:
                return tool_id

        return "general_query_tool"  # default tool

    def invoke_tool(self, tool, parameters):
        # Invoke the specified tool with the given parameters
        return tool.execute(parameters)

    def handle_request(self, request):
        tool = self.decide_tool(request)
        if tool:
            parameters = request.get("parameters", {})
            return self.invoke_tool(tool, parameters)
        else:
            raise ValueError("No suitable tool found for the request.")
