#!/usr/bin/env python3
"""
Render a Shipping LLMs article into Medium-pasteable HTML.

Usage:
    python3 scripts/to_medium.py 1            # render Part 1, open in browser
    python3 scripts/to_medium.py 1 --copy     # render Part 1 + copy rich HTML to clipboard
    python3 scripts/to_medium.py all          # render all 6 to disk (no browser)

After running with a part number:
    Browser opens the rendered article. Cmd+A, Cmd+C, then Cmd+V into Medium's body.
    The Medium title and subtitle fields are NOT in the clipboard, so the script
    prints them so you can paste them into Medium's title/subtitle fields directly.

The --copy flag attempts to put rich HTML on the macOS clipboard via textutil + pbcopy
so you can skip the browser step and just Cmd+V into Medium.

Renderer preference:
    1. pandoc (preferred, cleaner HTML)
    2. Python `markdown` library (pip3 install markdown)

Files written:
    output/<slug>/medium-paste.html   (the rendered article — open in any browser)
"""

import argparse
import re
import subprocess
import sys
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "output"

SLUGS = {
    1: "01-prompt-caching-vs-semantic-caching",
    2: "02-kv-cache-management-at-scale",
    3: "03-speculative-decoding-vs-quantization",
    4: "04-rag-evaluation-ragas-human-evals",
    5: "05-llm-cost-monitoring-hidden-token-leaks",
    6: "06-agent-guardrails-infinite-loop-detection",
}


# ---------- extraction ----------

def extract_article(part: int) -> tuple[str, str, str]:
    """Return (title, subtitle, body_markdown_without_h1) for the requested part."""
    folder = OUT / SLUGS[part]
    pkg_path = folder / "article_package.md"
    pkg = pkg_path.read_text(encoding="utf-8")

    # Subtitle from Quick Reference block
    sub_match = re.search(r"^- \*\*Subtitle\*\*: (.+)$", pkg, re.MULTILINE)
    subtitle = sub_match.group(1).strip() if sub_match else ""

    # FINAL ARTICLE section from the package
    body = ""
    m = re.search(
        r"## 1\. FINAL ARTICLE \(Ready to Paste into Medium\)\s*\n+(.+?)\n+---\n+## 2\.",
        pkg, re.DOTALL,
    )
    if m:
        body = m.group(1).strip()

    # If the package body has only the H1 (no real article content), fall back
    # to article_refiner.md. Detect "no real content" by looking for any
    # paragraph-like line after the H1.
    has_real_body = bool(re.search(r"^# .+?\n+\S", body, re.MULTILINE))
    if not has_real_body:
        refiner = folder / "article_refiner.md"
        if refiner.exists():
            r = refiner.read_text(encoding="utf-8")
            rm = re.search(r"## Final Article\s*\n+(.+)", r, re.DOTALL)
            if rm:
                body = rm.group(1).strip()

    if not body:
        sys.exit(f"Could not extract article body for Part {part}")

    h1_match = re.search(r"^# (.+)$", body, re.MULTILINE)
    title = h1_match.group(1).strip() if h1_match else ""
    body_without_h1 = re.sub(r"^# .+$\n*", "", body, count=1, flags=re.MULTILINE)
    return title, subtitle, body_without_h1.strip()


# ---------- markdown -> HTML ----------

DIAGRAM_MARKER_RE = re.compile(
    # Matches markers like:
    #   `[Diagram: ...]`           (Article 1's body)
    #   **[Insert Diagram: ...]**  (Articles 2-6)
    #   **[Insert Chart: ...]**
    #   **[Insert Infographic: ...]**
    #   **[Insert Dashboard Mockup]**
    #   **[Insert Table: ...]**    (these are SKIPPED — markdown handles tables)
    r'(?:[`*]+)\[(?:Insert\s+)?(Diagram|Chart|Infographic|Dashboard|Table)[^\]]*\](?:[`*]+)',
    re.IGNORECASE,
)


def replace_diagram_markers(md: str) -> str:
    """Replace diagram markers in markdown with unique tokens that survive
    pandoc rendering. We post-process the rendered HTML to swap them for
    <img> tags pointing at compiled PNGs. 'Table' markers are left alone.
    """
    counter = [0]

    def repl(match):
        kind = match.group(1).lower()
        if kind == "table":
            return match.group(0)
        counter[0] += 1
        # Pandoc preserves unknown text. Put on its own paragraph so it
        # becomes <p>TOKEN</p> in the rendered HTML, easy to swap out.
        return f"\n\nDIAGRAMASSETPLACEHOLDER{counter[0]:02d}\n\n"

    return DIAGRAM_MARKER_RE.sub(repl, md)


def md_to_html(md_text: str) -> str:
    # Replace diagram markers before rendering, so the placeholders flow
    # through pandoc as plain paragraphs and we can swap them post-render.
    md_text = replace_diagram_markers(md_text)

    raw = ""
    # Try pandoc first (cleaner output for Medium).
    try:
        result = subprocess.run(
            ["pandoc", "-f", "gfm+pipe_tables", "-t", "html",
             "--no-highlight", "--wrap=preserve"],
            input=md_text, capture_output=True, text=True, check=True,
        )
        raw = result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Fallback: python-markdown
        try:
            import markdown
            raw = markdown.markdown(
                md_text, extensions=["tables", "fenced_code", "sane_lists"],
            )
        except ImportError:
            sys.exit("Need pandoc (brew install pandoc) OR run: pip3 install markdown")

    # Strip pandoc's auto-added id attrs from headings (Medium occasionally
    # renders these as visible artifacts on paste).
    raw = re.sub(r'(<h[1-6])\s+id="[^"]*"', r'\1', raw)
    # Strip class attrs from headings/paragraphs (Medium ignores them anyway).
    raw = re.sub(r'(<(?:h[1-6]|p))\s+class="[^"]*"', r'\1', raw)
    # Some pandoc outputs include a header section before the content; strip it.
    raw = re.sub(r'<header[^>]*>.*?</header>', '', raw, flags=re.DOTALL)
    return raw


def embed_diagram_images(html: str) -> str:
    """Swap DIAGRAMASSETPLACEHOLDER01 / 02 / ... for <img> tags pointing at
    the per-article PNGs in ./assets/.
    """
    def make_img(n: int) -> str:
        return (
            f'<img src="assets/diagram-{n:02d}.png" alt="diagram {n}" '
            f'style="max-width:100%;height:auto;display:block;margin:1.5em auto;">'
        )

    # Pandoc wraps the placeholder in <p>...</p>; strip the wrapping.
    html = re.sub(
        r"<p>DIAGRAMASSETPLACEHOLDER(\d{2})</p>",
        lambda m: make_img(int(m.group(1))),
        html,
    )
    # Just in case it isn't wrapped.
    html = re.sub(
        r"DIAGRAMASSETPLACEHOLDER(\d{2})",
        lambda m: make_img(int(m.group(1))),
        html,
    )
    return html


# ---------- HTML shell ----------

CSS = """
  body { font-family: Georgia, serif; max-width: 700px; margin: 40px auto;
         padding: 0 20px; line-height: 1.7; color: #222; }
  h1   { font-size: 2.2em; line-height: 1.2; margin-bottom: 0.2em; }
  h2   { font-size: 1.6em; margin-top: 1.5em; }
  h3   { font-size: 1.25em; }
  pre  { background: #f5f5f5; padding: 1em; overflow-x: auto;
         border-radius: 4px; font-family: 'Menlo','Monaco',monospace; font-size: 0.9em; }
  code { background: #f0f0f0; padding: 0.1em 0.3em; border-radius: 3px;
         font-family: 'Menlo','Monaco',monospace; font-size: 0.92em; }
  pre code { background: transparent; padding: 0; }
  blockquote { border-left: 4px solid #ccc; margin-left: 0;
               padding-left: 1em; color: #555; }
  table { border-collapse: collapse; width: 100%; margin: 1em 0; }
  th, td { border: 1px solid #ddd; padding: 0.5em 0.8em; text-align: left; }
  th { background: #f8f8f8; }
  a { color: #1a73e8; }
  .subtitle { font-style: italic; color: #555; font-size: 1.15em;
              margin-top: 0; margin-bottom: 2em; }
"""


def wrap_html(title: str, subtitle: str, body_html: str, cover_exists: bool) -> str:
    # Title is the H1 at the top, subtitle styled italic below it, then the
    # cover image (if generated), then the article body. Cmd+A in the
    # browser grabs everything in one shot, which is what Medium's paste
    # expects.
    sub_html = f'<p class="subtitle">{subtitle}</p>\n' if subtitle else ""
    cover_html = (
        '<img src="assets/cover.png" alt="cover" '
        'style="max-width:100%;height:auto;display:block;margin:1em auto 2em;">\n'
        if cover_exists else ""
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<h1>{title}</h1>
{sub_html}{cover_html}{body_html}
</body>
</html>"""


# ---------- clipboard ----------

def copy_html_to_clipboard(html: str) -> bool:
    """Convert HTML to RTF via textutil, pipe to pbcopy.
    macOS apps that accept rich-text paste (including Medium) read this correctly."""
    try:
        rtf = subprocess.run(
            ["textutil", "-stdin", "-format", "html", "-convert", "rtf", "-stdout"],
            input=html.encode("utf-8"), capture_output=True, check=True,
        ).stdout
        subprocess.run(["pbcopy"], input=rtf, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


# ---------- top level ----------

def render(part: int, do_copy: bool, do_open: bool) -> Path:
    title, subtitle, body_md = extract_article(part)
    body_html = md_to_html(body_md)
    body_html = embed_diagram_images(body_html)

    folder = OUT / SLUGS[part]
    cover_exists = (folder / "assets" / "cover.png").exists()
    full_html = wrap_html(title, subtitle, body_html, cover_exists=cover_exists)

    out_path = folder / "medium-paste.html"
    out_path.write_text(full_html, encoding="utf-8")

    print(f"\n✓ Part {part}/6 rendered  →  {out_path.relative_to(REPO)}")
    print(f"  Medium Title:    {title}")
    if subtitle:
        print(f"  Medium Subtitle: {subtitle}")

    if do_copy:
        if copy_html_to_clipboard(full_html):
            print("  ✓ Rich text copied to clipboard. Cmd+V into Medium body.")
            return out_path
        print("  (clipboard copy failed, falling back to browser)")
        do_open = True

    if do_open:
        webbrowser.open(out_path.as_uri())
        print("  Browser opened. Cmd+A → Cmd+C → Cmd+V into Medium body.")
    return out_path


def main():
    p = argparse.ArgumentParser(description="Render a Shipping LLMs article to Medium-pasteable HTML.")
    p.add_argument("part", help="Part number 1-6, or 'all'")
    p.add_argument("--copy", action="store_true",
                   help="Copy rich text to clipboard (skip browser step)")
    p.add_argument("--no-open", action="store_true",
                   help="Don't open the browser (just write the HTML file)")
    args = p.parse_args()

    if args.part == "all":
        for i in range(1, 7):
            title, subtitle, body_md = extract_article(i)
            body_html = md_to_html(body_md)
            body_html = embed_diagram_images(body_html)
            folder = OUT / SLUGS[i]
            cover_exists = (folder / "assets" / "cover.png").exists()
            full_html = wrap_html(title, subtitle, body_html, cover_exists=cover_exists)
            out_path = folder / "medium-paste.html"
            out_path.write_text(full_html, encoding="utf-8")
            print(f"  ✓ Part {i}/6  →  {out_path.relative_to(REPO)}")
        print("\nAll 6 rendered. Open each medium-paste.html in browser when ready to publish.")
        return

    try:
        num = int(args.part)
        if num not in SLUGS:
            raise ValueError
    except ValueError:
        sys.exit(f"Part must be 1-6 or 'all', got {args.part!r}")

    render(num, do_copy=args.copy, do_open=not args.no_open)


if __name__ == "__main__":
    main()
