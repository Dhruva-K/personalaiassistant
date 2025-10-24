import unittest
from src.agents.base_agent import BaseAgent
from src.tools.tool_registry import ToolRegistry

class TestBaseAgent(unittest.TestCase):

    def setUp(self):
        self.agent = BaseAgent()
        self.tool_registry = ToolRegistry()
        self.agent.tool_registry = self.tool_registry

    def test_tool_invocation(self):
        # Assuming we have a mock tool to register
        mock_tool = lambda x: x * 2
        self.tool_registry.register_tool("mock_tool", mock_tool)

        # Test invoking the tool
        result = self.agent.invoke_tool("mock_tool", 5)
        self.assertEqual(result, 10)

    def test_tool_not_found(self):
        with self.assertRaises(ValueError):
            self.agent.invoke_tool("non_existent_tool", 5)

    def test_decision_making(self):
        # Mock decision-making logic
        self.agent.decide_tool = lambda request: "mock_tool" if request == "double" else None

        # Test decision-making
        tool_name = self.agent.decide_tool("double")
        self.assertEqual(tool_name, "mock_tool")

        tool_name = self.agent.decide_tool("unknown")
        self.assertIsNone(tool_name)

if __name__ == '__main__':
    unittest.main()