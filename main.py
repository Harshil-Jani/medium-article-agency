"""
Medium Content Agency — CLI Entry Point

Usage:
    python main.py --topic "Why Rust's borrow checker is a superpower"
    python main.py --topic "Rust vs Go for CLI tools" --model claude-sonnet-4-5-20250929
    python main.py --list
    python main.py --topic "..." --select trend_researcher technical_writer
"""

import argparse
import asyncio
import sys

from agents.definitions import AGENT_DEFINITIONS, get_agents_by_phase
from agents.orchestrator import ArticleOrchestrator
from config import DEFAULT_MODEL, FAST_MODEL, BALANCED_MODEL, ANTHROPIC_API_KEY


def list_agents():
    """Print all available agents and the pipeline structure."""
    phases = get_agents_by_phase()
    print("\nMedium Content Agency — Pipeline Agents\n")
    print("Pipeline Flow:")
    print("  Phase 0: Trend Researcher")
    print("      ↓")
    print("  Phase 1: Technical Writer")
    print("      ↓")
    print("  Phase 2: Editor + Graphic Designer (parallel)")
    print("      ↓")
    print("  Phase 3: Article Refiner")
    print("      ↓")
    print("  Phase 4: SEO Specialist + Social Media Manager (parallel)")
    print("      ↓")
    print("  Phase 5: Article Compiler")
    print()

    for phase_num, agents in phases.items():
        print(f"Phase {phase_num}:")
        for agent in agents:
            deps = (
                f" (depends on: {', '.join(agent.depends_on)})"
                if agent.depends_on
                else " (no dependencies)"
            )
            print(f"  • {agent.name:25s} — {agent.role}{deps}")
            print(
                f"    temp={agent.temperature}, "
                f"max_tokens={agent.max_tokens}"
            )
        print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Medium Content Agency — AI-powered article pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s --topic "Why Rust's borrow checker is a superpower"
  %(prog)s --topic "Comparing Rust and Go for CLI tools" --slug rust-vs-go-cli
  %(prog)s --topic "..." --model claude-sonnet-4-5-20250929
  %(prog)s --topic "..." --select trend_researcher technical_writer editor
  %(prog)s --list
        """,
    )

    parser.add_argument(
        "--topic",
        type=str,
        help="The article topic or idea to feed into the pipeline",
    )
    parser.add_argument(
        "--slug",
        type=str,
        default=None,
        help="Custom slug for the output directory (auto-generated if not provided)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        choices=[DEFAULT_MODEL, BALANCED_MODEL, FAST_MODEL],
        help=f"Model to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--select",
        nargs="+",
        type=str,
        default=None,
        help="Run only specific agents (dependencies auto-included)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all agents and pipeline structure",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output directory (default: output/)",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    if args.list:
        list_agents()
        return

    if not args.topic:
        print("Error: --topic is required (or use --list to see agents)")
        sys.exit(1)

    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY is not set.")
        print("Copy .env.example to .env and add your key.")
        sys.exit(1)

    # Validate selected agents
    if args.select:
        for name in args.select:
            if name not in AGENT_DEFINITIONS:
                print(
                    f"Error: Unknown agent '{name}'. "
                    f"Available: {', '.join(AGENT_DEFINITIONS.keys())}"
                )
                sys.exit(1)

    orchestrator = ArticleOrchestrator(
        model=args.model,
        selected_agents=args.select,
    )

    if args.output:
        orchestrator.output_dir = args.output

    output_dir = await orchestrator.run(
        topic=args.topic,
        topic_slug=args.slug,
    )

    print(f"Done! Article package saved to: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
