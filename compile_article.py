"""
Article Compiler — Assembles all agent outputs into a final publication package.

This script reads agent outputs from an output directory and compiles them
into a single, organized article_package.md ready for publication.

Usage:
    python compile_article.py output/rust-borrow-checker
    python compile_article.py output/rust-borrow-checker --format markdown
"""

import argparse
import json
import os
import sys
from datetime import datetime


def read_agent_output(run_dir: str, agent_name: str) -> str | None:
    """Read an agent's output file, returning None if not found."""
    filepath = os.path.join(run_dir, f"{agent_name}.md")
    if os.path.exists(filepath):
        with open(filepath) as f:
            return f.read().strip()
    return None


def extract_edited_article(editor_output: str) -> str:
    """
    Extract the edited article from the editor's output.

    The editor's output contains both review comments and the edited article.
    The edited article appears after '## Edited Article' or similar heading.
    """
    markers = [
        "## Edited Article",
        "## edited article",
        "## EDITED ARTICLE",
        "## Final Edited Article",
        "## Clean Version",
    ]

    lower_output = editor_output.lower()
    for marker in markers:
        pos = lower_output.find(marker.lower())
        if pos != -1:
            # Find the start of content after the heading
            newline_pos = editor_output.find("\n", pos)
            if newline_pos != -1:
                return editor_output[newline_pos:].strip()

    # Fallback: return the full editor output
    return editor_output


def extract_refined_article(refiner_output: str) -> str:
    """
    Extract the final article from the refiner's output.

    The refiner's output contains a changes summary followed by the final article
    after '## Final Article' or similar heading.
    """
    markers = [
        "## Final Article",
        "## final article",
        "## FINAL ARTICLE",
        "## Complete Final Article",
    ]

    lower_output = refiner_output.lower()
    for marker in markers:
        pos = lower_output.find(marker.lower())
        if pos != -1:
            newline_pos = refiner_output.find("\n", pos)
            if newline_pos != -1:
                return refiner_output[newline_pos:].strip()

    # Fallback: return the full refiner output
    return refiner_output


def compile_package(run_dir: str) -> str:
    """Compile all agent outputs into a single publication package."""
    # Read all agent outputs
    agents = {
        "trend_researcher": read_agent_output(run_dir, "trend_researcher"),
        "technical_writer": read_agent_output(run_dir, "technical_writer"),
        "editor": read_agent_output(run_dir, "editor"),
        "graphic_designer": read_agent_output(run_dir, "graphic_designer"),
        "article_refiner": read_agent_output(run_dir, "article_refiner"),
        "seo_specialist": read_agent_output(run_dir, "seo_specialist"),
        "social_media_manager": read_agent_output(run_dir, "social_media_manager"),
    }

    # Read summary if available
    summary_path = os.path.join(run_dir, "summary.json")
    summary = None
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            summary = json.load(f)

    # Extract the final article — prefer Refiner's version, fall back to Editor's, then Writer's
    final_article = ""
    if agents["article_refiner"]:
        final_article = extract_refined_article(agents["article_refiner"])
    elif agents["editor"]:
        final_article = extract_edited_article(agents["editor"])
    elif agents["technical_writer"]:
        final_article = agents["technical_writer"]

    # Build the package
    parts = []

    parts.append("# Article Publication Package")
    parts.append(f"\nCompiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if summary:
        parts.append(f"Model: {summary.get('model', 'unknown')}")
    parts.append("")

    # Quick reference
    parts.append("---\n")
    parts.append("## Quick Reference\n")
    parts.append(f"- **Author**: Harshil Jani")
    if summary:
        total_tokens = summary.get("total_input_tokens", 0) + summary.get(
            "total_output_tokens", 0
        )
        parts.append(
            f"- **Pipeline Duration**: {summary.get('total_duration', 'N/A')}s"
        )
        parts.append(f"- **Total Tokens**: {total_tokens:,}")
    parts.append("")

    # Final article
    parts.append("---\n")
    parts.append("## 1. FINAL ARTICLE\n")
    if final_article:
        parts.append(final_article)
    else:
        parts.append("*No article content available.*")
    parts.append("")

    # Editor review
    if agents["editor"]:
        parts.append("---\n")
        parts.append("## 2. EDITORIAL REVIEW\n")
        # Extract just the review part (before the edited article)
        editor_full = agents["editor"]
        lower = editor_full.lower()
        markers = ["## edited article", "## final edited article", "## clean version"]
        cut_pos = len(editor_full)
        for m in markers:
            pos = lower.find(m)
            if pos != -1 and pos < cut_pos:
                cut_pos = pos
        review_section = editor_full[:cut_pos].strip()
        parts.append(review_section)
        parts.append("")

    # Visual assets
    if agents["graphic_designer"]:
        parts.append("---\n")
        parts.append("## 3. VISUAL ASSETS\n")
        parts.append(agents["graphic_designer"])
        parts.append("")

    # SEO & Distribution
    if agents["seo_specialist"]:
        parts.append("---\n")
        parts.append("## 4. SEO & DISTRIBUTION\n")
        parts.append(agents["seo_specialist"])
        parts.append("")

    # Social media
    if agents["social_media_manager"]:
        parts.append("---\n")
        parts.append("## 5. SOCIAL MEDIA PACKAGE\n")
        parts.append(agents["social_media_manager"])
        parts.append("")

    # Trend research context
    if agents["trend_researcher"]:
        parts.append("---\n")
        parts.append("## 6. RESEARCH CONTEXT\n")
        parts.append(agents["trend_researcher"])
        parts.append("")

    # Pipeline summary
    if summary:
        parts.append("---\n")
        parts.append("## 7. PIPELINE SUMMARY\n")
        parts.append("| Agent | Duration | Tokens (in/out) |")
        parts.append("|---|---|---|")
        for name, info in summary.get("agents", {}).items():
            parts.append(
                f"| {info['role']} | {info['duration_seconds']}s | "
                f"{info['input_tokens']:,} / {info['output_tokens']:,} |"
            )
        parts.append("")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Compile agent outputs into a publication package"
    )
    parser.add_argument(
        "run_dir",
        help="Path to the output directory (e.g., output/rust-borrow-checker)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path (default: {run_dir}/article_package.md)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.run_dir):
        print(f"Error: Directory not found: {args.run_dir}")
        sys.exit(1)

    package = compile_package(args.run_dir)

    output_path = args.output or os.path.join(args.run_dir, "article_package.md")
    with open(output_path, "w") as f:
        f.write(package)

    print(f"Article package compiled: {output_path}")


if __name__ == "__main__":
    main()
