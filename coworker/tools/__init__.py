"""AI Co-worker tools package."""

from coworker.tools.search import search, wikipedia_lookup
from coworker.tools.notifications import send_push_notification
from coworker.tools.human_in_the_loop import request_human_help
from coworker.tools.presentation import create_presentation_slide, build_slide
from coworker.tools.mcp_sessions import McpSessions, mcp_connections


async def get_all_tools(sandbox: str):
    """Return the complete list of tools (local tools + persistent MCP tools) and the MCP session holder."""
    sessions = McpSessions(mcp_connections(sandbox))
    mcp_tools = await sessions.start()
    our_tools = [
        search,
        send_push_notification,
        wikipedia_lookup,
        request_human_help,
        create_presentation_slide,
    ]
    return our_tools + mcp_tools, sessions


__all__ = [
    "get_all_tools",
    "search",
    "send_push_notification",
    "wikipedia_lookup",
    "request_human_help",
    "create_presentation_slide",
    "build_slide",
    "McpSessions",
    "mcp_connections",
]
