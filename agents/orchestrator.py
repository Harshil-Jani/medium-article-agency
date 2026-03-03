"""
ArticleOrchestrator — DAG-based parallel pipeline runner for the Medium Content Agency.

Executes agents in phases, with agents in the same phase running concurrently.
Each agent receives the outputs of its dependencies via context injection.
"""

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime

import anthropic

from agents.definitions import (
    AgentDefinition,
    AGENT_DEFINITIONS,
    get_agents_by_phase,
)
from config import DEFAULT_MODEL, OUTPUT_DIR


@dataclass
class AgentResult:
    """Stores the output of a completed agent."""

    name: str
    role: str
    output: str
    duration_seconds: float
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ArticleOrchestrator:
    """
    Runs the Medium article pipeline by executing agents in DAG order.

    Agents are grouped by parallel_group. Within each group, all agents run
    concurrently via asyncio.gather(). Outputs are passed between agents
    through context injection — each agent receives the full output of every
    agent it depends on, prepended to its user message.
    """

    model: str = DEFAULT_MODEL
    api_key: str | None = None
    output_dir: str = OUTPUT_DIR
    event_queue: asyncio.Queue | None = None
    selected_agents: list[str] | None = None

    # Internal state
    results: dict[str, AgentResult] = field(default_factory=dict, init=False)
    client: anthropic.AsyncAnthropic = field(init=False)

    def __post_init__(self):
        kwargs = {}
        if self.api_key:
            kwargs["api_key"] = self.api_key
        self.client = anthropic.AsyncAnthropic(**kwargs)

    # ------------------------------------------------------------------
    # Event emission (for SSE / progress tracking)
    # ------------------------------------------------------------------

    async def _emit(self, event_type: str, data: dict):
        """Emit a structured event for progress tracking."""
        event = {"type": event_type, "timestamp": time.time(), **data}
        if self.event_queue:
            await self.event_queue.put(event)

    # ------------------------------------------------------------------
    # Context assembly
    # ------------------------------------------------------------------

    def _build_agent_context(self, agent: AgentDefinition, user_prompt: str) -> str:
        """
        Build the user message for an agent by injecting dependency outputs.

        Each agent receives:
        1. The original user prompt (topic idea)
        2. The full text output of every agent it depends on
        """
        context_parts = [f"## User Request\n{user_prompt}"]

        for dep_name in agent.depends_on:
            if dep_name in self.results:
                dep = self.results[dep_name]
                context_parts.append(
                    f"\n## Input from {dep.role}\n"
                    f"(This is the output from the {dep.role} agent — "
                    f"use it as your primary input)\n\n"
                    f"{dep.output}"
                )

        return "\n\n---\n\n".join(context_parts)

    # ------------------------------------------------------------------
    # Single agent execution
    # ------------------------------------------------------------------

    async def _run_agent(
        self, agent: AgentDefinition, user_prompt: str
    ) -> AgentResult:
        """Run a single agent and return its result."""
        await self._emit(
            "agent_start", {"agent": agent.name, "role": agent.role}
        )

        context = self._build_agent_context(agent, user_prompt)
        output_chunks: list[str] = []
        start_time = time.time()

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=agent.max_tokens,
                temperature=agent.temperature,
                system=agent.system_prompt,
                messages=[{"role": "user", "content": context}],
            ) as stream:
                async for text in stream.text_stream:
                    output_chunks.append(text)
                    # Emit progress every ~500 chars
                    if len(output_chunks) % 50 == 0:
                        await self._emit(
                            "agent_progress",
                            {
                                "agent": agent.name,
                                "chars": sum(len(c) for c in output_chunks),
                            },
                        )

                # Must be inside the async with block — stream closes on exit
                final_message = await stream.get_final_message()
                input_tokens = final_message.usage.input_tokens
                output_tokens = final_message.usage.output_tokens

        except Exception as e:
            await self._emit(
                "agent_error", {"agent": agent.name, "error": str(e)}
            )
            raise

        duration = time.time() - start_time
        output = "".join(output_chunks)

        result = AgentResult(
            name=agent.name,
            role=agent.role,
            output=output,
            duration_seconds=round(duration, 2),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        self.results[agent.name] = result
        await self._emit(
            "agent_done",
            {
                "agent": agent.name,
                "role": agent.role,
                "duration": result.duration_seconds,
                "output_length": len(output),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )

        return result

    # ------------------------------------------------------------------
    # Dependency resolution
    # ------------------------------------------------------------------

    def _resolve_agents(self) -> dict[int, list[AgentDefinition]]:
        """
        Resolve which agents to run, respecting dependencies.

        If selected_agents is set, include those agents plus all their
        transitive dependencies. Otherwise, run all agents.
        """
        if not self.selected_agents:
            return get_agents_by_phase()

        # Resolve transitive dependencies
        needed: set[str] = set()

        def _add_deps(name: str):
            if name in needed:
                return
            needed.add(name)
            agent = AGENT_DEFINITIONS[name]
            for dep in agent.depends_on:
                _add_deps(dep)

        for name in self.selected_agents:
            _add_deps(name)

        # Group resolved agents by phase
        phases: dict[int, list[AgentDefinition]] = {}
        for name in needed:
            agent = AGENT_DEFINITIONS[name]
            phases.setdefault(agent.parallel_group, []).append(agent)

        return dict(sorted(phases.items()))

    # ------------------------------------------------------------------
    # Output saving
    # ------------------------------------------------------------------

    def _save_outputs(self, topic_slug: str):
        """Save all agent outputs and a summary to the output directory."""
        run_dir = os.path.join(self.output_dir, topic_slug)
        os.makedirs(run_dir, exist_ok=True)

        # Save individual agent outputs
        for name, result in self.results.items():
            filepath = os.path.join(run_dir, f"{name}.md")
            with open(filepath, "w") as f:
                f.write(result.output)

        # Save summary
        summary = {
            "topic_slug": topic_slug,
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "agents": {
                name: {
                    "role": r.role,
                    "duration_seconds": r.duration_seconds,
                    "output_length": len(r.output),
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                }
                for name, r in self.results.items()
            },
            "total_duration": sum(r.duration_seconds for r in self.results.values()),
            "total_input_tokens": sum(r.input_tokens for r in self.results.values()),
            "total_output_tokens": sum(
                r.output_tokens for r in self.results.values()
            ),
        }

        with open(os.path.join(run_dir, "summary.json"), "w") as f:
            json.dump(summary, f, indent=2)

        # Save combined report
        combined = []
        for name, result in self.results.items():
            combined.append(f"{'=' * 60}")
            combined.append(f"# {result.role}")
            combined.append(f"Agent: {result.name} | Duration: {result.duration_seconds}s")
            combined.append(f"{'=' * 60}\n")
            combined.append(result.output)
            combined.append("\n")

        with open(os.path.join(run_dir, "full_report.md"), "w") as f:
            f.write("\n".join(combined))

        return run_dir

    # ------------------------------------------------------------------
    # Main pipeline runner
    # ------------------------------------------------------------------

    async def run(self, topic: str, topic_slug: str | None = None) -> str:
        """
        Run the full article pipeline for a given topic.

        Args:
            topic: The article topic or idea from the user.
            topic_slug: Optional slug for the output directory.
                        Auto-generated from topic if not provided.

        Returns:
            Path to the output directory.
        """
        if not topic_slug:
            # Generate filesystem-safe slug from topic
            topic_slug = re.sub(r"[^a-z0-9-]", "-", topic.lower())
            topic_slug = re.sub(r"-+", "-", topic_slug)  # collapse dashes
            topic_slug = "-".join(topic_slug.split("-")[:8]).strip("-")

        phases = self._resolve_agents()
        total_agents = sum(len(agents) for agents in phases.values())

        await self._emit(
            "pipeline_start",
            {
                "topic": topic,
                "topic_slug": topic_slug,
                "model": self.model,
                "total_phases": len(phases),
                "total_agents": total_agents,
            },
        )

        print(f"\n{'=' * 60}")
        print(f"  Medium Content Agency — Article Pipeline")
        print(f"  Topic: {topic}")
        print(f"  Model: {self.model}")
        print(f"  Phases: {len(phases)} | Agents: {total_agents}")
        print(f"{'=' * 60}\n")

        pipeline_start = time.time()

        for phase_num, agents in phases.items():
            agent_names = ", ".join(a.role for a in agents)
            print(f"▶ Phase {phase_num}: {agent_names}")
            await self._emit(
                "phase_start",
                {
                    "phase": phase_num,
                    "agents": [a.name for a in agents],
                },
            )

            # Run all agents in this phase concurrently
            tasks = [self._run_agent(agent, topic) for agent in agents]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for errors
            failed_agents = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    agent = agents[i]
                    print(f"  ✗ {agent.role} FAILED: {result}")
                    failed_agents.append(agent)
                    await self._emit(
                        "agent_error",
                        {"agent": agent.name, "error": str(result)},
                    )
                else:
                    print(
                        f"  ✓ {result.role} done ({result.duration_seconds}s, "
                        f"{result.output_tokens} tokens)"
                    )

            # Stop pipeline if any agent in this phase failed —
            # downstream agents would run with missing context
            if failed_agents:
                failed_names = ", ".join(a.role for a in failed_agents)
                raise RuntimeError(
                    f"Pipeline halted: {failed_names} failed in phase {phase_num}. "
                    f"Downstream agents cannot proceed without their output."
                )

            await self._emit("phase_done", {"phase": phase_num})
            print()

        pipeline_duration = round(time.time() - pipeline_start, 2)

        # Save outputs
        run_dir = self._save_outputs(topic_slug)

        total_input = sum(r.input_tokens for r in self.results.values())
        total_output = sum(r.output_tokens for r in self.results.values())

        print(f"{'=' * 60}")
        print(f"  Pipeline complete in {pipeline_duration}s")
        print(f"  Tokens: {total_input:,} input + {total_output:,} output")
        print(f"  Output: {run_dir}")
        print(f"{'=' * 60}\n")

        await self._emit(
            "pipeline_done",
            {
                "duration": pipeline_duration,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "output_dir": run_dir,
            },
        )

        return run_dir
