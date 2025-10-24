import unittest
from src.tools.tool_registry import ToolRegistry

class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()

    def test_register_tool(self):
        self.registry.register_tool("test_tool", lambda x: x)
        self.assertIn("test_tool", self.registry.tools)

    def test_retrieve_tool(self):
        self.registry.register_tool("test_tool", lambda x: x)
        tool = self.registry.get_tool("test_tool")
        self.assertIsNotNone(tool)
        self.assertEqual(tool("test"), "test")

    def test_retrieve_nonexistent_tool(self):
        tool = self.registry.get_tool("nonexistent_tool")
        self.assertIsNone(tool)

if __name__ == "__main__":
    unittest.main()