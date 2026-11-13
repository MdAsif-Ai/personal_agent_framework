"""Tests for AI Co-Worker agent architecture and evaluation models."""

import unittest
from coworker.agent import EvaluatorOutput, CoworkerAgent, Coworker, TolerateToolErrors
from langchain_core.messages import ToolMessage


class TestAgent(unittest.IsolatedAsyncioTestCase):
    def test_evaluator_output_schema(self):
        """Verify EvaluatorOutput validation."""
        output = EvaluatorOutput(
            feedback="Criteria met thoroughly.",
            success_criteria_met=True,
            user_input_needed=False,
        )
        self.assertTrue(output.success_criteria_met)
        self.assertFalse(output.user_input_needed)
        self.assertIn("thoroughly", output.feedback)

    async def test_tolerate_tool_errors_middleware(self):
        """Verify TolerateToolErrors middleware gracefully catches exceptions and returns ToolMessage."""
        middleware = TolerateToolErrors()

        class DummyRequest:
            tool_call = {"id": "tool_123", "name": "failing_tool"}

        async def failing_handler(req):
            raise ValueError("Simulated network timeout")

        result = await middleware.awrap_tool_call(DummyRequest(), failing_handler)
        self.assertIsInstance(result, ToolMessage)
        self.assertEqual(result.tool_call_id, "tool_123")
        self.assertIn("Simulated network timeout", result.content)

    async def test_agent_empty_message_handling(self):
        """Verify that submitting an empty message does not crash or execute turns."""
        agent = CoworkerAgent()
        history = [{"role": "user", "content": "hello"}]
        result = await agent.run_turn("", "Criteria", history=history)
        self.assertEqual(result, history)

        result_none = await agent.run_turn("   ", "Criteria", history=None)
        self.assertEqual(result_none, [])

    def test_alias(self):
        """Verify that Coworker is an alias of CoworkerAgent."""
        self.assertIs(Coworker, CoworkerAgent)


if __name__ == "__main__":
    unittest.main()
