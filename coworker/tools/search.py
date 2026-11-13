"""Information retrieval and search tools."""

import logging
import wikipedia
from langchain_community.tools import GoogleSerperRun, WikipediaQueryRun
from langchain_community.utilities import GoogleSerperAPIWrapper, WikipediaAPIWrapper
from langchain_core.tools import tool

from coworker.config import SERPER_API_KEY

logger = logging.getLogger(__name__)

# Wikimedia requires a descriptive User-Agent header
wikipedia.set_user_agent("agentic-coworker (https://edwarddonner.com)")

# Setup Wikipedia lookup tool
wikipedia_lookup = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Setup Google Serper search tool with graceful fallback if key is missing
if SERPER_API_KEY:
    try:
        search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper(serper_api_key=SERPER_API_KEY))
    except Exception as e:
        logger.warning(f"Error initializing GoogleSerperRun: {e}")

        @tool
        def search(query: str) -> str:
            """Search Google for up-to-date information, news, and facts."""
            return f"Search error: Google Serper is unavailable ({e}). Please use Wikipedia or the browser directly."

else:
    logger.info("SERPER_API_KEY not configured. Using fallback search tool.")

    @tool
    def search(query: str) -> str:
        """Search Google for up-to-date information, news, and facts."""
        return (
            "SERPER_API_KEY environment variable is not configured. "
            "Please use the Wikipedia tool or navigate directly using the browser."
        )
