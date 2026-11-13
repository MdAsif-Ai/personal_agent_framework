"""Root entry point for the AI Co-Worker Gradio application.

Run with:
    uv run app.py
"""

from coworker.ui.app import (
    ui,
    launch,
    setup_agent as setup,
    process_message,
    approve_action as approve,
    watch_todos,
    reset_session as reset,
    free_resources,
    render_todos,
)
from coworker.ui.theme import LAUNCH_STYLE, HEADER_HTML as HEADER

if __name__ == "__main__":
    launch()
