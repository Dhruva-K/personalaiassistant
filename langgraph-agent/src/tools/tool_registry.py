from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseTool(ABC):
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute the tool with given parameters"""
        pass


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool_id: str, tool: BaseTool) -> None:
        """Register a new tool"""
        if tool_id in self._tools:
            raise ValueError(f"Tool with ID '{tool_id}' is already registered.")
        self._tools[tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Get a tool by its ID"""
        tool = self._tools.get(tool_id)
        if tool is None:
            raise ValueError(f"Tool with ID '{tool_id}' is not registered.")
        return tool

    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self._tools.keys())


# Tool implementations
class EmailTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Implement email functionality
        return {"status": "success", "message": "Email sent successfully"}


class PDFTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Implement PDF handling functionality
        return {"status": "success", "message": "PDF processed successfully"}


class CalendarTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Implement calendar functionality
        return {"status": "success", "message": "Meeting scheduled successfully"}


class SearchTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Implement search functionality
        return {"status": "success", "message": "Search completed successfully"}


class OrderTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Implement pizza ordering functionality
        return {"status": "success", "message": "Pizza order placed successfully"}


class GeneralQueryTool(BaseTool):
    def execute(self, parameters: Dict[str, Any]) -> Any:
        # Handle general queries
        return {"status": "success", "message": "I can help you with emails, PDFs, scheduling, searching, or ordering pizza. What would you like to do?"}


def create_tool_registry() -> ToolRegistry:
    """Create and initialize the tool registry with all available tools"""
    registry = ToolRegistry()

    # Register all tools
    registry.register_tool("email_tool", EmailTool())
    registry.register_tool("pdf_tool", PDFTool())
    registry.register_tool("calendar_tool", CalendarTool())
    registry.register_tool("search_tool", SearchTool())
    registry.register_tool("order_tool", OrderTool())
    registry.register_tool("general_query_tool", GeneralQueryTool())

    return registry
