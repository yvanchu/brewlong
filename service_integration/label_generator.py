"""Generate 1-bit monochrome label PNGs for the NIIMBOT B1."""

import logging
import os
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .config import LABEL_HEIGHT_PX, LABEL_WIDTH_PX

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Label pixel dimensions (portrait: short edge = width, long edge = height)
# ---------------------------------------------------------------------------
WIDTH = LABEL_HEIGHT_PX   # 30 mm → 239 px
HEIGHT = LABEL_WIDTH_PX   # 50 mm → 399 px

# ---------------------------------------------------------------------------
# Font sizes (in pixels)
# ---------------------------------------------------------------------------
NAME_FONT_SIZE = 30
MOD_FONT_SIZE = 30
ORDER_FONT_SIZE = 42

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
PADDING = 10
TOP_MARGIN = 40
SEPARATOR_GAP = 10
MAX_NAME_LINES = 4
MAX_MOD_LINES = 6

# ---------------------------------------------------------------------------
# Font discovery (macOS-first, with Linux fallbacks)
# ---------------------------------------------------------------------------
_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]

_BOLD_CANDIDATES = [
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def _load_font(candidates: list[str], size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try each candidate path and return the first loadable font."""
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            if path.endswith(".ttc"):
                # Helvetica.ttc: index 0 = regular, index 1 = bold
                return ImageFont.truetype(path, size, index=1 if bold else 0)
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    logger.warning("No system font found; falling back to default bitmap font")
    return ImageFont.load_default(size)


def generate_label(
    item_name: str,
    modifiers: list[str],
    order_number: str,
    output_dir: str = ".",
) -> Path:
    """Render a single drink label and return the path to the saved PNG.

    Layout (top → bottom):
        1. Item name  — 30 px bold, up to 2 wrapped lines
        2. Separator  — thin horizontal rule
        3. Modifiers  — 22 px regular, up to 4 bullet lines
        4. Order #    — 42 px bold, centred at bottom
    """
    img = Image.new("1", (WIDTH, HEIGHT), color=1)  # 1-bit white
    draw = ImageDraw.Draw(img)

    name_font = _load_font(_BOLD_CANDIDATES, NAME_FONT_SIZE, bold=True)
    mod_font = _load_font(_REGULAR_CANDIDATES, MOD_FONT_SIZE, bold=False)
    order_font = _load_font(_BOLD_CANDIDATES, ORDER_FONT_SIZE, bold=True)

    y = TOP_MARGIN

    # ── 1. Item name (up to 2 wrapped lines) ──────────────────────────────
    usable_width = WIDTH - 2 * PADDING
    # Estimate max chars per line from average character width
    avg_char_w = draw.textlength("M", font=name_font)
    max_chars = max(int(usable_width / avg_char_w), 4)
    wrapped = textwrap.wrap(item_name, width=max_chars) or [item_name]

    for line in wrapped[:MAX_NAME_LINES]:
        draw.text((PADDING, y), line, font=name_font, fill=0)
        bbox = draw.textbbox((PADDING, y), line, font=name_font)
        y = bbox[3] + 2

    # ── 2. Separator line ──────────────────────────────────────────────────
    y += SEPARATOR_GAP
    draw.line([(PADDING, y), (WIDTH - PADDING, y)], fill=0, width=1)
    y += SEPARATOR_GAP + 2

    # ── 3. Modifiers (up to 4 bullet lines) ────────────────────────────────
    for mod in modifiers[:MAX_MOD_LINES]:
        text = f"• {mod}"
        draw.text((PADDING, y), text, font=mod_font, fill=0)
        bbox = draw.textbbox((PADDING, y), text, font=mod_font)
        y = bbox[3] + 2

    # ── 4. Order number (bold, horizontally centred, pinned to bottom) ─────
    order_text = f"{order_number}"
    bbox = draw.textbbox((0, 0), order_text, font=order_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y_order = HEIGHT - text_h - PADDING
    draw.text((x, y_order), order_text, font=order_font, fill=0)

    # ── Save ───────────────────────────────────────────────────────────────
    output_path = Path(output_dir) / f"temp_label_{order_number}.png"
    img.save(output_path)
    logger.info("Label saved → %s", output_path)
    return output_path
