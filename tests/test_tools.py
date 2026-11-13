"""Tests for AI Co-Worker tools and presentation generation."""

import tempfile
import unittest
from pathlib import Path
from coworker.tools.notifications import send_push_notification
from coworker.tools.human_in_the_loop import request_human_help
from coworker.tools.search import search
from coworker.tools.presentation import build_slide


class TestTools(unittest.TestCase):
    def test_push_notification_simulation_fallback(self):
        """Verify that send_push_notification does not raise an exception when credentials are not set."""
        result = send_push_notification.invoke({"text": "Test push message"})
        self.assertTrue("Simulated Push Notification" in result or "Notification sent" in result)

    def test_request_human_help(self):
        """Verify human help tool response."""
        result = request_human_help.invoke({"instructions": "Please solve captcha"})
        self.assertTrue("completed" in result.lower() or "continue" in result.lower())

    def test_search_tool_callable(self):
        """Verify search tool handles invocation without crashing."""
        result = search.invoke({"query": "Python programming"})
        self.assertIsInstance(result, str)

    def test_build_slide_creates_pptx(self):
        """Verify presentation slide generation writes a valid pptx file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "test_slide.pptx"
            title = "Fleet pick: Tesla Model Y"
            key_points = [
                "Lowest total cost of ownership at $0.42/mile",
                "Superior supercharger network accessibility",
                "Highest resale retention in class",
            ]
            recommendation = "Voltway recommends Tesla Model Y over Hyundai Ioniq 5."

            build_slide(title, key_points, recommendation, output_file)

            self.assertTrue(output_file.exists())
            self.assertGreater(output_file.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
