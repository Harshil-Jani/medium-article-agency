# Medium Content Agency

A multi-agent AI pipeline that produces publication-ready Medium articles for Harshil Jani's technical content brand.

## What It Does

Give it a topic idea → Get back a complete article publication package:

- Trend-validated article (800-1,000 words)
- Editorial review with quality scoring
- Cover image + inline graphic specifications
- SEO-optimized metadata and distribution plan
- Ready-to-post social media content (Twitter, LinkedIn, Reddit, HN)

## The Pipeline

```
Researcher → Writer → Editor + Designer → Refiner → SEO + Social Media → Compiler
 (Phase 0)  (Phase 1)    (Phase 2)       (Phase 3)     (Phase 4)        (Phase 5)
```

**8 agents, 6 phases.** Agents within the same phase run in parallel.

| Agent | Phase | Role |
|---|---|---|
| Trend Researcher | 0 | Scans trending topics, validates relevance |
| Technical Writer | 1 | Writes the article in Harshil's voice |
| Editor | 2 | Reviews article, provides critique and line edits |
| Graphic Designer | 2 | Creates Excalidraw/draw.io visual specs |
| Article Refiner | 3 | Applies Editor's feedback, produces final article |
| SEO Specialist | 4 | Optimizes metadata, plans distribution |
| Social Media Manager | 4 | Creates promotion content for all platforms |
| Article Compiler | 5 | Assembles final publication package |

## Two Ways to Run

### 1. Claude Code Mode (Recommended)

Open this project in Claude Code and describe your article idea. Claude reads `CLAUDE.md` and runs the full pipeline, acting as each agent sequentially.

```bash
# Just open the project and talk
claude
> Write an article about why Rust's borrow checker is actually a superpower for systems programming
```

### 2. CLI Mode (API-driven)

Run programmatically with parallel execution via the Anthropic API.

```bash
# Setup
cp .env.example .env  # Add your ANTHROPIC_API_KEY
./run.sh --topic "Why Rust's borrow checker is a superpower"

# Or manually
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py --topic "Why Rust's borrow checker is a superpower"
```

#### CLI Options

```
--topic TEXT       Article topic/idea (required)
--slug TEXT        Custom output directory slug
--model MODEL     claude-opus-4-6 (default) | claude-sonnet-4-5-20250929 | claude-haiku-4-5-20251001
--select AGENTS   Run specific agents (dependencies auto-included)
--list            Show all agents and pipeline structure
--output DIR      Custom output directory
```

#### Examples

```bash
# Full pipeline
python main.py --topic "Comparing Rust and Go for CLI tools"

# Just research + writing (no SEO/social media)
python main.py --topic "Rust error handling patterns" --select trend_researcher technical_writer editor

# Faster model for drafts
python main.py --topic "..." --model claude-sonnet-4-5-20250929

# List all agents
python main.py --list
```

## Output Structure

```
output/
└── rust-borrow-checker/
    ├── trend_researcher.md      # Topic brief
    ├── technical_writer.md      # Draft article
    ├── editor.md                # Editorial review + feedback
    ├── graphic_designer.md      # Excalidraw/draw.io visual specs
    ├── article_refiner.md       # Final polished article
    ├── seo_specialist.md        # SEO metadata + distribution plan
    ├── social_media_manager.md  # Promotion package
    ├── article_package.md       # Final compiled package
    ├── full_report.md           # All outputs combined
    └── summary.json             # Pipeline metadata + token usage
```

## Post-Pipeline Compilation

After the pipeline runs, compile everything into a single package:

```bash
python compile_article.py output/rust-borrow-checker
```

## Agency Niche

**Topics**: Rust, open source, systems programming, fintech, Bitcoin/crypto, developer tooling

**Voice**: Clear, opinionated, practical, first-person — like explaining to a smart colleague over coffee

**Cadence**: 2 articles/week on Medium

## Project Structure

```
├── agents/
│   ├── definitions.py              # Agent configs (prompts, dependencies, phases)
│   ├── orchestrator.py             # DAG-based parallel pipeline runner
│   ├── trend-researcher.md         # Agent prompt (Claude Code mode)
│   ├── technical-writer.md         # Agent prompt
│   ├── editor.md                   # Agent prompt
│   ├── graphic-designer.md         # Agent prompt (Excalidraw/draw.io)
│   ├── article-refiner.md          # Agent prompt (applies Editor feedback)
│   ├── seo-specialist.md           # Agent prompt
│   ├── social-media-manager.md     # Agent prompt
│   ├── article-compiler.md         # Agent prompt
│   └── medium-article-generator.md # Full pipeline orchestrator prompt
├── config/
│   └── __init__.py                 # Model config, API key, agency settings
├── main.py                         # CLI entry point
├── compile_article.py              # Post-pipeline article assembler
├── run.sh                          # One-command runner
├── CLAUDE.md                       # Claude Code mode instructions
├── requirements.txt                # Python dependencies
└── output/                         # Generated articles (gitignored)
```

## License

MIT
