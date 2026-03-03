# CLAUDE.md — Medium Content Agency

## What This Is
This is Harshil Jani's Medium Content Agency — a multi-agent pipeline that produces publication-ready Medium articles. You are the orchestrator.

## How It Works
When the user provides a topic, you act as each of the 8 specialist agents in sequence, producing a complete article publication package.

## The Pipeline

```
Phase 0: Trend Researcher       → Topic brief with ranked suggestions
    ↓
Phase 1: Technical Writer       → 800-1,000 word draft article
    ↓
Phase 2: Editor + Graphic Designer → Editorial review + visual specs (parallel)
    ↓
Phase 3: Article Refiner        → Final polished article (applies Editor's feedback)
    ↓
Phase 4: SEO + Social Media     → Metadata + promotion plan (parallel)
    ↓
Phase 5: Article Compiler       → Final publication package
```

## Running the Pipeline

For each phase:
1. Read the agent's prompt file from `agents/`
2. Act as that agent, following all instructions in the prompt
3. Save the output to `output/{topic-slug}/{agent_name}.md`
4. Move to the next phase

### Phase 0 — Research
- Read `agents/trend-researcher.md`
- If user gave a specific topic: validate it and produce a focused brief
- If user wants suggestions: produce full ranked brief
- Save to `output/{slug}/trend_researcher.md`

### Phase 1 — Write
- Read `agents/technical-writer.md`
- Use the Trend Researcher output as input
- Write 800-1,000 word article in Harshil's voice
- Save to `output/{slug}/technical_writer.md`

### Phase 2 — Review & Visuals
- Read `agents/editor.md` — Review article (critique only, no rewrite)
- Read `agents/graphic-designer.md` — Create Excalidraw/draw.io visual specifications
- Save to `output/{slug}/editor.md` and `output/{slug}/graphic_designer.md`

### Phase 3 — Refinement
- Read `agents/article-refiner.md` — Apply Editor's feedback to produce final article
- Save to `output/{slug}/article_refiner.md`

### Phase 4 — Distribution
- Read `agents/seo-specialist.md` — Optimize metadata, plan distribution
- Read `agents/social-media-manager.md` — Create promotion package
- Save to `output/{slug}/seo_specialist.md` and `output/{slug}/social_media_manager.md`

### Phase 5 — Compile
- Read `agents/article-compiler.md` — Assemble everything
- Save to `output/{slug}/article_package.md`

## Quality Gate
After the Editor phase, check the quality score:
- **A or B**: Continue to Phase 3 (Refinement)
- **C**: Proceed but note concerns for the Refiner
- **D or F**: Stop and ask the user — article needs a rewrite, not just refinement

## Brand Voice
Harshil's voice: clear, opinionated, practical, first-person. Like explaining to a smart colleague over coffee. No corporate jargon, no filler.

## Niche
Rust, open source, systems programming, fintech, Bitcoin/crypto, developer tooling.

## CLI Mode
The pipeline also runs programmatically via `python main.py --topic "..."`. See README.md for details.
