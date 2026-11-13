"""Slide generator module (root level export).

Provides backwards compatibility with notebooks and scripts importing from `slide_kit`.
"""

from coworker.tools.presentation import (
    build_slide,
    create_presentation_slide,
    NAVY,
    TEAL,
    WHITE,
    MIST,
    DEFAULT_LOGO as LOGO,
)

__all__ = [
    "build_slide",
    "create_presentation_slide",
    "NAVY",
    "TEAL",
    "WHITE",
    "MIST",
    "LOGO",
]
