"""
Reusable cover-image template for the Shipping LLMs series.

Each article's assets/cover.py imports `make_cover` from here and calls it
with that article's part number, title, subtitle, and accent emoji/icon.

Output is a 1500x750 PNG that fits Medium's recommended cover ratio.

Design language (matches graphic_designer.md brand):
    - Off-white background (#F8F9FA)
    - Series badge top-right ("SHIPPING LLMs · PART N/6")
    - Big title bottom-left, Inter Bold-style
    - Two-color accent bar at bottom (blue + orange)
    - Subtle "shipping" pun: a stylized cargo/box icon top-left
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Brand palette (from agents/graphic-designer.md)
BG = (248, 249, 250)        # off-white
DARK = (45, 45, 45)         # text
BLUE = (26, 115, 232)       # primary
ORANGE = (255, 107, 53)     # accent
GREEN = (52, 168, 83)       # success
MUTED = (130, 130, 130)     # subdued text

WIDTH, HEIGHT = 1500, 750


def _find_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    """Try candidate font paths in order; fall back to default if none load."""
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _bold(size: int) -> ImageFont.FreeTypeFont:
    return _find_font([
        "/System/Library/Fonts/Helvetica.ttc",       # macOS
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ], size)


def _regular(size: int) -> ImageFont.FreeTypeFont:
    return _find_font([
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ], size)


def _wrap(text: str, font, draw, max_width: int) -> list[str]:
    """Wrap text into lines that fit max_width pixels."""
    words = text.split()
    lines: list[str] = []
    line = ""
    for w in words:
        candidate = (line + " " + w).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def make_cover(
    part: int,
    title: str,
    subtitle: str,
    output_path: Path,
    accent_text: str = "",
) -> Path:
    """Render a cover PNG. Returns the output path."""
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # Top accent bar (thin)
    draw.rectangle([0, 0, WIDTH, 8], fill=BLUE)

    # Series badge (top-right)
    badge_font = _bold(28)
    badge_text = f"SHIPPING LLMs  ·  PART {part}/6"
    bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = bbox[2] - bbox[0]
    draw.text(
        (WIDTH - badge_w - 60, 50),
        badge_text,
        font=badge_font,
        fill=DARK,
    )

    # Decorative "shipping box" icon top-left (simple geometric)
    box_x, box_y, box_size = 60, 50, 70
    draw.rectangle(
        [box_x, box_y, box_x + box_size, box_y + box_size],
        outline=BLUE,
        width=4,
    )
    # cross lines on top (like a tape mark)
    draw.line(
        [box_x, box_y + box_size // 3, box_x + box_size, box_y + box_size // 3],
        fill=BLUE,
        width=3,
    )
    draw.line(
        [box_x + box_size // 2, box_y, box_x + box_size // 2, box_y + box_size // 3],
        fill=BLUE,
        width=3,
    )

    # Title (large, bottom-left zone)
    title_font = _bold(78)
    title_lines = _wrap(title, title_font, draw, max_width=WIDTH - 120)

    # Anchor title at vertical center-bottom
    line_height = 92
    total_title_h = line_height * len(title_lines)
    title_top = HEIGHT - 300 - total_title_h + line_height // 2
    for i, line in enumerate(title_lines):
        draw.text((60, title_top + i * line_height), line, font=title_font, fill=DARK)

    # Subtitle (smaller, below title)
    sub_font = _regular(34)
    sub_lines = _wrap(subtitle, sub_font, draw, max_width=WIDTH - 140)
    sub_top = title_top + total_title_h + 30
    for i, line in enumerate(sub_lines):
        draw.text(
            (60, sub_top + i * 44),
            line,
            font=sub_font,
            fill=MUTED,
        )

    # Bottom two-color accent bar
    bar_y = HEIGHT - 80
    bar_h = 12
    draw.rectangle([0, bar_y, WIDTH // 2, bar_y + bar_h], fill=BLUE)
    draw.rectangle([WIDTH // 2, bar_y, WIDTH, bar_y + bar_h], fill=ORANGE)

    # Author + accent text bottom-right (small)
    foot_font = _regular(22)
    foot = f"@harshil_jani28   ·   {accent_text}" if accent_text else "@harshil_jani28"
    bbox = draw.textbbox((0, 0), foot, font=foot_font)
    draw.text(
        (WIDTH - (bbox[2] - bbox[0]) - 60, bar_y - 50),
        foot,
        font=foot_font,
        fill=MUTED,
    )

    img.save(output_path, format="PNG", optimize=True)
    return output_path
