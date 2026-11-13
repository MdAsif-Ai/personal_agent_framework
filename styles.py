"""Styling module (root level export).

Provides backwards compatibility with notebooks and scripts importing from `styles`.
"""

from coworker.ui.theme import (
    THEME,
    CSS,
    JS,
    NAVY,
    BLUE,
    GOLD,
    PURPLE,
    GRAY,
    BACKGROUND,
    LAUNCH_STYLE,
    HEADER_HTML as HEADER,
)

__all__ = [
    "THEME",
    "CSS",
    "JS",
    "NAVY",
    "BLUE",
    "GOLD",
    "PURPLE",
    "GRAY",
    "BACKGROUND",
    "LAUNCH_STYLE",
    "HEADER",
]
