"""Slide deck generator for Voltway Research presentation style."""

import os
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt
from langchain_core.tools import tool

from coworker.config import SANDBOX_DIR

NAVY = RGBColor(0x0A, 0x25, 0x40)
TEAL = RGBColor(0x00, 0xC2, 0xA8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
MIST = RGBColor(0xB9, 0xC4, 0xD0)

DEFAULT_LOGO = SANDBOX_DIR / "skills" / "fleet-slide" / "logo.png"


def _textbox(slide, left: float, top: float, width: float, height: float,
             text: str, size: int, color: RGBColor, bold: bool = False, spacing: float | None = None):
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    frame = box.text_frame
    frame.word_wrap = True
    para = frame.paragraphs[0]
    run = para.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    if spacing is not None:
        para.line_spacing = spacing
    return box


def build_slide(title: str, key_points: list[str], recommendation: str, outfile: str | Path,
                logo_path: str | Path | None = None) -> None:
    """Build the one-slide Voltway recommendation deck and save it to outfile.

    Args:
        title: Slide headline (names the pick in 5 words or fewer).
        key_points: List of 3 key takeaway bullet points.
        recommendation: Concluding recommendation sentence.
        outfile: Output file destination (.pptx).
        logo_path: Optional path to logo image. Defaults to standard fleet-slide logo.
    """
    out_path = Path(outfile)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Slide background
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = NAVY

    # Add logo if present
    logo_file = Path(logo_path) if logo_path else DEFAULT_LOGO
    if logo_file.exists():
        slide.shapes.add_picture(str(logo_file), Inches(0.5), Inches(0.45), Inches(0.55), Inches(0.55))

    _textbox(slide, 1.2, 0.52, 6, 0.5, "VOLTWAY  RESEARCH", 15, MIST, bold=True)
    _textbox(slide, 0.5, 1.55, 12.3, 1.2, title, 34, WHITE, bold=True)

    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.53), Inches(2.55), Inches(2.2), Inches(0.05))
    rule.fill.solid()
    rule.fill.fore_color.rgb = TEAL
    rule.line.fill.background()

    for i, point in enumerate(key_points[:3]):
        y = 3.05 + i * 0.72
        marker = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(y + 0.1), Inches(0.16), Inches(0.16))
        marker.fill.solid()
        marker.fill.fore_color.rgb = TEAL
        marker.line.fill.background()
        _textbox(slide, 0.95, y, 11.8, 0.6, point, 17, WHITE)

    _textbox(slide, 0.53, 5.55, 6, 0.4, "VOLTWAY RECOMMENDS", 12, TEAL, bold=True)
    banner = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(5.95), Inches(12.33), Inches(1.05))
    banner.adjustments[0] = 0.18
    banner.fill.solid()
    banner.fill.fore_color.rgb = TEAL
    banner.line.fill.background()
    frame = banner.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    frame.margin_left = Inches(0.35)
    frame.margin_right = Inches(0.35)
    para = frame.paragraphs[0]
    run = para.add_run()
    run.text = recommendation
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = NAVY

    prs.save(str(out_path))


@tool
def create_presentation_slide(title: str, key_points: list[str], recommendation: str, filename: str = "fleet.pptx") -> str:
    """Create a one-slide PowerPoint presentation in the Voltway Research house style and save it in the sandbox.

    Args:
        title: Headline naming the choice in under 35 characters (e.g. 'Fleet pick: Tesla Model Y').
        key_points: Exactly three bullet points with concrete metrics/numbers.
        recommendation: One sentence stating the decision and naming the runner-up.
        filename: Destination file name (defaults to 'fleet.pptx').
    """
    target = SANDBOX_DIR / filename
    build_slide(title, key_points, recommendation, target)
    return f"Saved presentation slide to {target.name}"

