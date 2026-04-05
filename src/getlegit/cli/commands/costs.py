"""legit costs — display estimated LLM API cost history."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

THEME = "#7F77DD"


def _load_entries() -> list[dict]:
    """Load all cost log entries from .legit/costs.json."""
    cost_path = Path.cwd() / ".legit" / "costs.json"
    if not cost_path.exists():
        return []
    try:
        data = json.loads(cost_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _current_month_key() -> str:
    now = datetime.now(timezone.utc)
    return f"{now.year}-{now.month:02d}"


@click.command("costs")
def costs_command() -> None:
    """Display estimated LLM API costs from Layer 2 scoring."""
    entries = _load_entries()

    if not entries:
        console.print(
            f"\n[{THEME}]No cost data yet.[/{THEME}] "
            "Costs are logged when you run [bold]legit submit[/bold] with Layer 2 API keys.\n"
        )
        return

    # Filter to current month
    month_key = _current_month_key()
    month_entries = [
        e for e in entries
        if e.get("timestamp", "")[:7] == month_key
    ]

    # Aggregate by model
    model_totals: dict[str, float] = {}
    grand_total = 0.0
    for e in month_entries:
        for model, cost in e.get("models", {}).items():
            model_totals[model] = model_totals.get(model, 0.0) + cost
            grand_total += cost

    all_time_total = sum(e.get("total", 0.0) for e in entries)
    submit_count = len(month_entries)
    avg_cost = grand_total / submit_count if submit_count else 0.0

    console.print()
    console.print(
        Panel(
            "",
            title=f"[bold {THEME}]Estimated LLM Costs ({month_key})[/bold {THEME}]",
            border_style=THEME,
            width=50,
        )
    )

    # Print summary directly since Rich table-in-panel is tricky
    console.print(f"  Submits this month: [bold]{submit_count}[/bold]")
    console.print(f"  Average per submit: [bold]${avg_cost:.4f}[/bold]")
    console.print()

    if model_totals:
        console.print("  [bold]Breakdown by model:[/bold]")
        for model, cost in sorted(model_totals.items()):
            console.print(f"    {model:<20} ${cost:.4f}")
        console.print()

    console.print(f"  Month total:    [bold]${grand_total:.4f}[/bold]")
    console.print(f"  All-time total: [bold]${all_time_total:.4f}[/bold]")
    console.print()

    console.print(
        "  [dim]Costs are estimates based on approximate token counts.[/dim]\n"
        "  [dim]Actual costs depend on your LLM provider pricing.[/dim]\n"
    )
