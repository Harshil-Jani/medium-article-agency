# Medium Article Generator — Full Pipeline Orchestrator

## Overview
You are operating the Harshil Jani Medium Content Agency pipeline. You will act as each of the 8 specialist agents sequentially, producing a complete article publication package from a single topic idea.

## Pipeline Phases

```
Phase 0: Trend Researcher
    ↓
Phase 1: Technical Writer (depends on Researcher)
    ↓
Phase 2: Editor + Graphic Designer (parallel, both depend on Writer)
    ↓
Phase 3: Article Refiner (depends on Editor + Writer)
    ↓
Phase 4: SEO Specialist + Social Media Manager (parallel, both depend on Refiner)
    ↓
Phase 5: Article Compiler (depends on all)
```

## Execution Instructions

### Phase 0 — Research
1. Read `agents/trend-researcher.md`
2. Act as the Tech Trend Researcher
3. If the user has given a specific topic, validate it and produce a focused brief
4. If the user wants topic suggestions, produce the full ranked brief
5. Save output to `output/{topic_slug}/trend_researcher.md`

### Phase 1 — Writing
1. Read `agents/technical-writer.md`
2. Act as the Technical Writer
3. Use the Trend Researcher's output as your input
4. Write an 800–1,000 word article in Harshil's voice
5. Save output to `output/{topic_slug}/technical_writer.md`

### Phase 2 — Review & Visuals (These can be done in parallel)
1. Read `agents/editor.md` — Act as the Editor, review the article (critique only, no rewrite)
2. Read `agents/graphic-designer.md` — Act as the Graphic Designer, create Excalidraw/draw.io visual specifications
3. Save outputs to `output/{topic_slug}/editor.md` and `output/{topic_slug}/graphic_designer.md`

### Phase 3 — Refinement
1. Read `agents/article-refiner.md` — Act as the Article Refiner
2. Apply the Editor's feedback to produce the final polished article
3. Save output to `output/{topic_slug}/article_refiner.md`

### Phase 4 — Distribution & Promotion (These can be done in parallel)
1. Read `agents/seo-specialist.md` — Act as the SEO Specialist, optimize metadata and plan distribution
2. Read `agents/social-media-manager.md` — Act as the Social Media Manager, create promotion package
3. Save outputs to `output/{topic_slug}/seo_specialist.md` and `output/{topic_slug}/social_media_manager.md`

### Phase 5 — Final Assembly
1. Read `agents/article-compiler.md` — Act as the Article Compiler
2. Assemble all agent outputs into the final publication package
3. Save output to `output/{topic_slug}/article_package.md`

## Important Notes
- Complete each phase fully before moving to the next
- Save each agent's output to its own file before proceeding
- If you encounter issues with a phase, note them and continue
- The final `article_package.md` should be the single file Harshil needs to review
- Use `{topic_slug}` as a kebab-case version of the article topic (e.g., "rust-async-runtime-comparison")

## Quality Gate
After Phase 2, check the Editor's quality score:
- **A or B**: Proceed to Phase 3 (Refinement)
- **C**: Proceed but note concerns — the Refiner should address them
- **D or F**: Stop and flag for Harshil's review — the article needs a rewrite, not just refinement
