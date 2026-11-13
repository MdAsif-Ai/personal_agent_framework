"""Tests for UI helpers and rendering."""

import unittest
from coworker.ui.app import render_todos


class TestUI(unittest.TestCase):
    def test_render_todos_empty(self):
        html = render_todos([])
        self.assertIn("The AI Co-Worker will write its plan here", html)
        self.assertIn("Plan", html)

    def test_render_todos_with_items(self):
        todos = [
            {"content": "Search flights on Google", "status": "completed"},
            {"content": "Compare round-trip prices", "status": "in_progress"},
            {"content": "Send push notification", "status": "pending"},
        ]
        html = render_todos(todos)
        self.assertIn("Search flights on Google", html)
        self.assertIn("completed", html)
        self.assertIn("in_progress", html)
        self.assertIn("pending", html)


if __name__ == "__main__":
    unittest.main()
