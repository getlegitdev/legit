"""Benchmark task execution engine."""

from __future__ import annotations

import json
import random
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from getlegit.cli.config import LegitConfig, results_dir
from getlegit.judges.layer1.verifier import verify_task
from getlegit.judges.scoring import calculate_scores

console = Console()

MAX_RETRIES = 3
RETRY_DELAY = 10


@dataclass
class TaskResult:
    task_id: str
    variant: str
    category: str
    level: int
    agent_response: dict[str, Any] | None
    layer1: dict[str, Any]
    agent_metadata: dict[str, Any]
    error: str | None = None
    layer1_weight: float | None = None
    layer2_weight: float | None = None


@dataclass
class BenchmarkResults:
    version: str
    agent_name: str
    tasks: list[TaskResult] = field(default_factory=list)
    total_score: float = 0.0
    category_scores: dict[str, float] = field(default_factory=dict)
    total_duration: float = 0.0
    failed_count: int = 0


def _find_tasks_dir(version: str) -> Path:
    """Locate the bundled benchmark tasks directory."""
    pkg_dir = Path(__file__).resolve().parent.parent
    tasks_dir = pkg_dir / "benchmarks" / version / "tasks"
    return tasks_dir


def _load_tasks(version: str) -> list[dict[str, Any]]:
    """Load all task definitions from the benchmarks directory."""
    tasks_dir = _find_tasks_dir(version)
    if not tasks_dir.exists():
        console.print(
            f"[bold yellow]Warning:[/bold yellow] No tasks found at {tasks_dir}. "
            "Benchmark tasks may not be installed yet."
        )
        return []

    tasks = []
    for task_file in sorted(tasks_dir.glob("*/task.json")):
        try:
            data = json.loads(task_file.read_text(encoding="utf-8"))
            data["_task_dir"] = str(task_file.parent)
            tasks.append(data)
        except (json.JSONDecodeError, OSError) as exc:
            console.print(f"[yellow]Skipping {task_file}: {exc}[/yellow]")
    return tasks


def _pick_variant(task: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Select a random variant from a task definition and load its data from disk."""
    variant_ids = task.get("variants", ["a"])
    if isinstance(variant_ids, dict):
        # Already loaded variant data (legacy)
        variant_id = random.choice(list(variant_ids.keys()))
        return variant_id, {**task, **variant_ids[variant_id]}

    variant_id = random.choice(variant_ids)
    task_dir = task.get("_task_dir", "")
    if task_dir:
        variant_file = Path(task_dir) / "variants" / f"{variant_id}.json"
        if variant_file.exists():
            variant_data = json.loads(variant_file.read_text(encoding="utf-8"))
            return variant_id, {**task, **variant_data}
    return variant_id, task


def _build_payload(task: dict[str, Any], variant_id: str) -> dict[str, Any]:
    """Build the request payload to send to the agent."""
    return {
        "task_id": task.get("task_id", "unknown"),
        "variant": variant_id,
        "task_description": task.get("task_description", ""),
        "input_data": task.get("input_data", {}),
        "output_schema": task.get("output_schema", {}),
        "time_limit_seconds": task.get("time_limit_seconds", 600),
        "allowed_tools": task.get("allowed_tools", []),
    }


def _send_to_agent(
    endpoint: str,
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any] | None:
    """Send task payload to agent with retries. Returns response dict or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(endpoint, json=payload)
                resp.raise_for_status()
                return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException, Exception) as exc:
            if attempt < MAX_RETRIES:
                console.print(
                    f"  [yellow]Attempt {attempt}/{MAX_RETRIES} failed: {exc}. "
                    f"Retrying in {RETRY_DELAY}s...[/yellow]"
                )
                time.sleep(RETRY_DELAY)
            else:
                console.print(
                    f"  [red]All {MAX_RETRIES} attempts failed: {exc}[/red]"
                )
    return None


class BenchmarkRunner:
    """Runs benchmark tasks against an agent and scores results."""

    def __init__(self, config: LegitConfig, version: str = "v1") -> None:
        self.config = config
        self.version = version

    def run(self) -> BenchmarkResults:
        tasks = _load_tasks(self.version)
        results = BenchmarkResults(
            version=self.version,
            agent_name=self.config.agent.name,
        )

        if not tasks:
            console.print("[bold yellow]No tasks to run.[/bold yellow]")
            return results

        # Filter by category if configured
        selected_categories = self.config.benchmark.categories
        if "all" not in selected_categories:
            tasks = [
                t for t in tasks
                if t.get("category", "").lower() in [c.lower() for c in selected_categories]
            ]

        # Auto-start mock server if any tasks are in the "operate" category
        mock_server = None
        mock_thread = None
        has_operate_tasks = any(
            t.get("category", "").lower() == "operate" for t in tasks
        )
        if has_operate_tasks:
            try:
                from getlegit.benchmarks.v1.mock_server import create_server, reset_state

                reset_state()
                mock_server = create_server(port=9999)
                mock_thread = threading.Thread(
                    target=mock_server.serve_forever, daemon=True
                )
                mock_thread.start()
                console.print(
                    "[dim]Mock server started on localhost:9999 for Operate tasks[/dim]"
                )
            except Exception as exc:
                console.print(
                    f"[bold yellow]Warning:[/bold yellow] Could not start mock server: {exc}"
                )
                mock_server = None

        console.print(
            f"\n[bold #7F77DD]Legit[/bold #7F77DD] evaluating "
            f"[bold]{self.config.agent.name}[/bold] "
            f"with {len(tasks)} tasks\n"
        )

        with Progress(
            SpinnerColumn(style="#7F77DD"),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="#7F77DD"),
            console=console,
        ) as progress:
            overall = progress.add_task("Running tasks...", total=len(tasks))

            for task_def in tasks:
                variant_id, variant_data = _pick_variant(task_def)
                task_id = task_def.get("task_id", "unknown")
                category = task_def.get("category", "unknown")
                level = task_def.get("level", 1)
                task_dir = task_def.get("_task_dir", "")

                progress.update(overall, description=f"Task {task_id} ({category})")

                payload = _build_payload(variant_data, variant_id)
                start = time.time()
                agent_resp = _send_to_agent(
                    self.config.agent.endpoint,
                    payload,
                    self.config.agent.timeout,
                )
                elapsed = time.time() - start

                # Per-task layer weights from the task definition
                task_l1w = task_def.get("layer1_weight")
                task_l2w = task_def.get("layer2_weight")

                if agent_resp is None:
                    # Agent unreachable — record failure
                    task_result = TaskResult(
                        task_id=task_id,
                        variant=variant_id,
                        category=category,
                        level=level,
                        agent_response=None,
                        layer1={"score": 0, "checks": []},
                        agent_metadata={
                            "duration_seconds": round(elapsed, 1),
                            "steps_taken": 0,
                            "tools_used": [],
                            "error_count": 1,
                        },
                        error="Agent unreachable after retries",
                        layer1_weight=task_l1w,
                        layer2_weight=task_l2w,
                    )
                    results.failed_count += 1
                else:
                    # Run Layer 1 verification
                    metadata = agent_resp.get("metadata", {})
                    agent_output = agent_resp.get("output", {})
                    duration = metadata.get("duration_seconds", round(elapsed, 1))

                    l1_result = verify_task(
                        task_def=variant_data,
                        agent_output=agent_output,
                        agent_metadata=metadata,
                        task_dir=Path(task_dir) if task_dir else None,
                        variant_id=variant_id,
                    )

                    task_result = TaskResult(
                        task_id=task_id,
                        variant=variant_id,
                        category=category,
                        level=level,
                        agent_response=agent_resp,
                        layer1=l1_result,
                        agent_metadata={
                            "duration_seconds": duration,
                            "steps_taken": metadata.get("steps_taken", 0),
                            "tools_used": metadata.get("tools_used", []),
                            "error_count": metadata.get("error_count", 0),
                        },
                        layer1_weight=task_l1w,
                        layer2_weight=task_l2w,
                    )

                results.tasks.append(task_result)
                results.total_duration += task_result.agent_metadata["duration_seconds"]
                progress.advance(overall)

        # Shut down mock server if it was started
        if mock_server is not None:
            try:
                mock_server.shutdown()
                console.print("[dim]Mock server stopped[/dim]")
            except Exception:
                pass

        # Calculate scores
        results = calculate_scores(results)

        # Save results
        self._save_results(results)

        return results

    def _save_results(self, results: BenchmarkResults) -> None:
        """Persist individual task results and summary to disk."""
        rd = results_dir(self.config)

        for tr in results.tasks:
            result_data = {
                "task_id": tr.task_id,
                "variant": tr.variant,
                "category": tr.category,
                "level": tr.level,
                "agent_response": tr.agent_response,
                "layer1": tr.layer1,
                "agent_metadata": tr.agent_metadata,
                "error": tr.error,
                "layer1_weight": tr.layer1_weight,
                "layer2_weight": tr.layer2_weight,
            }
            (rd / f"{tr.task_id}.json").write_text(
                json.dumps(result_data, indent=2),
                encoding="utf-8",
            )

        summary = {
            "version": results.version,
            "agent_name": results.agent_name,
            "total_score": round(results.total_score, 1),
            "category_scores": {
                k: round(v, 1) for k, v in results.category_scores.items()
            },
            "total_duration": round(results.total_duration, 1),
            "task_count": len(results.tasks),
            "failed_count": results.failed_count,
        }
        (rd / "_summary.json").write_text(
            json.dumps(summary, indent=2),
            encoding="utf-8",
        )
