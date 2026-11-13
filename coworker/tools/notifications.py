"""Push notification tools for alerting the user."""

import logging
import requests
from langchain_core.tools import tool

from coworker.config import PUSHOVER_TOKEN, PUSHOVER_USER

logger = logging.getLogger(__name__)


@tool
def send_push_notification(text: str) -> str:
    """Send a short push notification to the user's phone via Pushover."""
    if not PUSHOVER_TOKEN or not PUSHOVER_USER:
        logger.warning("PUSHOVER_TOKEN or PUSHOVER_USER not set. Simulating push notification.")
        return f"[Simulated Push Notification] {text} (Note: Pushover credentials not configured)"

    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "message": text,
            },
            timeout=10,
        )
        response.raise_for_status()
        return "Notification sent successfully"
    except requests.RequestException as e:
        logger.error(f"Failed to send push notification: {e}")
        return f"Push notification service error: {e}"

