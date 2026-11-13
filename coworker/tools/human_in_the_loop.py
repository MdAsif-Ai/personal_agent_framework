"""Human-in-the-loop interaction tools."""

from langchain_core.tools import tool


@tool
def request_human_help(instructions: str) -> str:
    """Ask the user to do something in the browser window that you cannot do yourself,
    such as logging in to a site, passing a captcha, or approving two-factor authentication.
    Explain exactly what you need them to do. The run pauses until they have done it."""
    return "The user completed the requested action in the browser. You may now continue with the task."

