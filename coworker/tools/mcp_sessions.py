"""Model Context Protocol (MCP) persistent session management."""

import asyncio
import logging
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from coworker.config import MCP_BROWSER_ISOLATED

logger = logging.getLogger(__name__)

# Apply Windows subprocess pipe adjustment if running on Windows
if sys.platform == "win32":
    import subprocess
    from functools import partial
    import langchain_mcp_adapters.sessions as mcp_sessions

    mcp_sessions.stdio_client = partial(mcp_sessions.stdio_client, errlog=subprocess.DEVNULL)


def mcp_connections(sandbox: str | Path) -> dict:
    """Return connection settings for Playwright and Filesystem MCP servers."""
    sandbox_path = str(Path(sandbox).resolve())
    playwright_args = ["@playwright/mcp@latest"]
    if MCP_BROWSER_ISOLATED:
        playwright_args.append("--isolated")

    return {
        "playwright": {
            "transport": "stdio",
            "command": "npx",
            "args": playwright_args,
        },
        "filesystem": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", sandbox_path],
        },
    }


class McpSessions:
    """Manages persistent MCP server sessions so state (like browser tabs and cookies) persists across tool calls.

    Because stdio transport requires connection and cleanup within the same asyncio task,
    a background task maintains the sessions alive until stop() or aclose() is invoked.
    """

    def __init__(self, connections: dict):
        self.connections = connections
        self.tools = []
        self._ready = asyncio.Event()
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def _run(self):
        client = MultiServerMCPClient(self.connections)
        try:
            async with AsyncExitStack() as stack:
                loaded_tools = []
                for name in self.connections:
                    try:
                        session = await stack.enter_async_context(client.session(name))
                        server_tools = await load_mcp_tools(session, server_name=name)
                        loaded_tools.extend(server_tools)
                    except Exception as server_err:
                        logger.error(f"Failed to start MCP server '{name}': {server_err}")
                        raise
                self.tools = loaded_tools
                self._ready.set()
                await self._stop.wait()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in MCP session background task: {e}")
            self._ready.set()
            raise

    async def start(self) -> list:
        """Start the background task and wait until MCP tools are loaded."""
        self._task = asyncio.create_task(self._run())
        ready = asyncio.create_task(self._ready.wait())
        await asyncio.wait([ready, self._task], return_when=asyncio.FIRST_COMPLETED)
        ready.cancel()

        if self._task.done():
            # Server task finished unexpectedly; retrieve exception
            exc = self._task.exception()
            if exc:
                raise exc
        return self.tools

    def stop(self):
        """Signal the MCP sessions to terminate (synchronous)."""
        self._stop.set()

    async def aclose(self):
        """Asynchronously stop sessions and wait for server shutdown."""
        self.stop()
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()

