from typing import TypedDict, List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from ..tools.tool_registry import ToolRegistry
from ..agents.base_agent import BaseAgent


class AgentState(TypedDict):
    """State for the agent's execution"""

    messages: List[BaseMessage]
    current_tool: str
    tool_output: Dict[str, Any]
    next_step: str


class StateManager:
    def __init__(self, agent: BaseAgent, tool_registry: ToolRegistry):
        self.agent = agent
        self.tool_registry = tool_registry
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        """Create the state graph for the agent"""

        # Define the workflow graph
        workflow = StateGraph(AgentState)

        # Add nodes for each step in the workflow
        workflow.add_node("process_input", self._process_input)
        workflow.add_node("execute_tool", self._execute_tool)
        workflow.add_node("generate_response", self._generate_response)

        # Define the edges between nodes
        workflow.add_edge("process_input", "execute_tool")
        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("generate_response", END)

        # Compile the graph
        return workflow.compile()

    def _process_input(self, state: AgentState) -> AgentState:
        """Process the input and determine the next tool to use"""
        # Get the latest message
        latest_message = state["messages"][-1]

        # Use the agent to decide which tool to use
        tool = self.agent.decide_tool({"input": latest_message.content})

        return {**state, "current_tool": tool, "next_step": "execute_tool"}

    def _execute_tool(self, state: AgentState) -> AgentState:
        """Execute the selected tool"""
        tool = self.tool_registry.get_tool(state["current_tool"])
        result = tool.execute({"input": state["messages"][-1].content})

        return {**state, "tool_output": result, "next_step": "generate_response"}

    def _generate_response(self, state: AgentState) -> AgentState:
        """Generate the final response based on tool output"""
        # Add the tool output to the message history
        new_messages = state["messages"] + [
            AIMessage(content=str(state["tool_output"]))
        ]

        return {**state, "messages": new_messages, "next_step": END}

    def run(self, user_input: str) -> str:
        """Run the agent workflow with the given user input"""
        initial_state = AgentState(
            messages=[HumanMessage(content=user_input)],
            current_tool="",
            tool_output={},
            next_step="process_input",
        )

        final_state = self.graph.invoke(initial_state)
        return final_state["messages"][-1].content
