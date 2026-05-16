#!/usr/bin/env python3
"""
Compile per-article visual assets (covers + inline diagrams) into PNG files.

Pipeline phase 5.5: runs after article_refiner + graphic_designer have produced
the final article and the visual specs. The graphic_designer agent should
output not just the prose spec but also the corresponding source files
(Mermaid for flows, matplotlib for charts, Pillow for covers) under
output/<slug>/assets/.

Source file conventions in output/<slug>/assets/:
    cover.py             → produces cover.png (Pillow or matplotlib script)
    diagram-01.mmd       → Mermaid flow/architecture, rendered via mmdc
    diagram-01.py        → Python script that writes diagram-01.png
    diagram-02.{mmd,py}  → second diagram, etc.

Usage:
    python3 scripts/compile_assets.py 1        # one article
    python3 scripts/compile_assets.py all      # all 6
"""

import argparse
import subprocess
import sys
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


def render_mermaid(src: Path, png: Path) -> None:
    """Render .mmd file to .png via mermaid-cli (mmdc)."""
    cmd = [
        "mmdc", "-i", str(src), "-o", str(png),
        "-b", "white",
        "-w", "1400",
        "-s", "2",
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def render_python_script(src: Path) -> None:
    """Run a Python script that produces a PNG in its own directory.

    The script is responsible for writing its own output PNG. We just run it.
    """
    subprocess.run(
        [sys.executable, str(src.name)],
        cwd=str(src.parent),
        check=True,
        capture_output=True,
        text=True,
    )


def compile_article(part: int) -> list[Path]:
    """Compile all assets for one article. Returns list of generated PNGs."""
    folder = OUT / SLUGS[part]
    assets = folder / "assets"
    if not assets.exists():
        print(f"  - no assets/ folder for Part {part}, skipping")
        return []

    generated: list[Path] = []

    for src in sorted(assets.iterdir()):
        if src.suffix == ".mmd":
            png = src.with_suffix(".png")
            try:
                render_mermaid(src, png)
                print(f"  ✓ rendered {png.relative_to(REPO)} (mermaid)")
                generated.append(png)
            except subprocess.CalledProcessError as e:
                print(f"  ✗ mermaid failed for {src.name}:")
                print(f"    {e.stderr}")
        elif src.suffix == ".py":
            try:
                render_python_script(src)
                png = src.with_suffix(".png")
                if png.exists():
                    print(f"  ✓ rendered {png.relative_to(REPO)} (python)")
                    generated.append(png)
                else:
                    print(f"  ✗ {src.name} ran but didn't produce {png.name}")
            except subprocess.CalledProcessError as e:
                print(f"  ✗ python script failed for {src.name}:")
                print(f"    {e.stderr}")

    return generated


def main():
    p = argparse.ArgumentParser(description="Compile graphic-designer specs to PNG assets.")
    p.add_argument("part", help="Part number 1-6, or 'all'")
    args = p.parse_args()

    if args.part == "all":
        for i in range(1, 7):
            print(f"\n== Part {i}/6 ==")
            compile_article(i)
    else:
        try:
            num = int(args.part)
            if num not in SLUGS:
                raise ValueError
        except ValueError:
            sys.exit(f"Part must be 1-6 or 'all', got {args.part!r}")
        print(f"\n== Part {num}/6 ==")
        compile_article(num)


if __name__ == "__main__":
    main()
