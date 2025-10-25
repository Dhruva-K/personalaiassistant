from typing import List, Dict, Any, Optional, Union
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import re
import time


class BaseAgent:
    """Base agent class with clarification and uncertainty handling."""
    
    def __init__(self, tool_registry, model_name: str = "mistral", temperature: float = 0.1):
        """Initialize agent with tool registry and language model."""
        self.tool_registry = tool_registry
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            streaming=True,
        )
        self.context = []
        self.confidence_threshold = 0.8
        self.max_clarification_turns = 3

        # Define the base prompt template
        self.base_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a personal AI assistant that can help with various tasks:
            1. Writing and sending emails
            2. Reading and analyzing PDF files
            3. Scheduling meetings
            4. Searching the internet
            5. Ordering pizzas
            
            You must:
            - Always protect private information
            - Ask for clarification when uncertain
            - Use local processing for private data
            - Be clear about your capabilities and limitations"""),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}"),
        ])
        
    def _detect_uncertainty(self, response: str) -> bool:
        """
        Detect if the response indicates uncertainty.
        
        Args:
            response: Model's response text
            
        Returns:
            bool: True if uncertainty is detected
        """
        uncertainty_patterns = [
            r"i'm not sure",
            r"i don't know",
            r"could you clarify",
            r"need more information",
            r"unclear",
            r"ambiguous",
            r"(?:can|could) you specify",
            r"what do you mean by",
            r"please provide more details",
        ]
        
        for pattern in uncertainty_patterns:
            if re.search(pattern, response.lower()):
                return True
                
        return False
        
    def _generate_clarifying_question(self, user_input: str, context: List[Dict]) -> str:
        """
        Generate a clarifying question based on input and context.
        
        Args:
            user_input: User's input text
            context: Conversation context
            
        Returns:
            str: Clarifying question
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Given the user's input and conversation context, generate a specific clarifying question to resolve any ambiguity or gather missing information. Focus on one aspect at a time and make the question clear and direct."""),
            ("user", f"User input: {user_input}\nContext: {context}"),
        ])
        
        response = self.llm.invoke(prompt.format_messages())
        return response.content
        
    def _extract_key_details(self, text: str) -> Dict[str, Any]:
        """
        Extract key details from text to identify missing information.
        
        Args:
            text: Input text to analyze
            
        Returns:
            dict: Extracted details and confidence scores
        """
        # Example patterns to extract common details
        patterns = {
            "time": r"\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b",
            "date": r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
        }
        
        details = {}
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text)
            details[key] = {
                "found": bool(matches),
                "value": matches[0] if matches else None,
                "confidence": 1.0 if matches else 0.0
            }
            
        return details
        
    def parse_tool_selection(self, llm_response: str) -> str:
        """Parse LLM response to determine which tool to use."""
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
        
    def decide_tool(self, request: Dict[str, Any]) -> Any:
        """
        Decide which tool to use based on the request.
        
        Args:
            request: User request details
            
        Returns:
            Tool instance to use
        """
        input_text = request.get("input", "")
        
        # Check for uncertainty
        if self._detect_uncertainty(input_text):
            question = self._generate_clarifying_question(input_text, self.context)
            self.update_context("agent", question, {"type": "clarification"})
            return None
            
        # Extract and check required details
        details = self._extract_key_details(input_text)
        missing_required = any(
            not detail["found"] 
            for detail in details.values()
        )
        
        if missing_required:
            question = self._generate_clarifying_question(input_text, self.context)
            self.update_context("agent", question, {"type": "clarification"})
            return None
            
        # Format prompt and get tool selection
        messages = self.base_prompt.format_messages(
            input=input_text,
            agent_scratchpad=""
        )
        
        response = self.llm.invoke(messages)
        tool_id = self.parse_tool_selection(response.content)
        return self.tool_registry.get_tool(tool_id)
        
    def invoke_tool(self, tool, parameters: Dict[str, Any]) -> Any:
        """
        Invoke a tool with parameters.
        
        Args:
            tool: Tool instance to invoke
            parameters: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        try:
            result = tool.execute(parameters)
            self.update_context("tool", str(result), {
                "tool_id": tool.__class__.__name__,
                "parameters": parameters
            })
            return result
        except Exception as e:
            error_msg = f"Error invoking tool: {str(e)}"
            self.update_context("error", error_msg, {
                "tool_id": tool.__class__.__name__,
                "parameters": parameters
            })
            raise
            
    def handle_request(self, request: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """
        Handle a user request with uncertainty handling.
        
        Args:
            request: User request details
            
        Returns:
            Response string or result dictionary
        """
        self.update_context("user", request.get("input", ""))
        
        clarification_count = 0
        while clarification_count < self.max_clarification_turns:
            tool = self.decide_tool(request)
            
            if tool is None:
                # Need clarification
                clarification_count += 1
                clarification = self._generate_clarifying_question(
                    request.get("input", ""),
                    self.context
                )
                return {"type": "clarification", "question": clarification}
                
            try:
                parameters = request.get("parameters", {})
                result = self.invoke_tool(tool, parameters)
                return {"type": "result", "data": result}
                
            except Exception as e:
                return {
                    "type": "error",
                    "message": str(e)
                }
                
        # If we've exceeded clarification turns, make best effort
        tool = self.tool_registry.get_tool("general_query_tool")
        return self.invoke_tool(tool, request.get("parameters", {}))
        
    def update_context(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Update conversation context.
        
        Args:
            role: Role of the speaker (user/agent/tool/error)
            content: Content of the message
            metadata: Optional metadata about the message
        """
        self.context.append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": time.time()
        })
        
    def clear_context(self) -> None:
        """Clear conversation context."""
        self.context = []
