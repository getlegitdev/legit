"""legit explain command — show detailed results for a task."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from getlegit.cli.config import load_config, results_dir

console = Console()

HINT_MAP: dict[str, str] = {
    "schema_valid": "Ensure your output matches the JSON schema specified in the task.",
    "required_fields": "Make sure all required fields are present and non-empty.",
    "min_count": "Array fields may need a minimum number of items — check the task spec.",
    "numeric_accuracy": "Numeric values must be within the specified tolerance of ground truth.",
    "code_parses": "Code outputs must parse without syntax errors (AST check).",
    "time_check": "Try to respond faster — you exceeded the time limit.",
    "keyword_present": "Include expected keywords or phrases in your output.",
}


@click.command("explain")
@click.argument("task_id")
def explain_command(task_id: str) -> None:
    """Show detailed Layer 1 results for a specific task."""
    try:
        config = load_config()
    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

    rd = results_dir(config)
    result_file = rd / f"{task_id}.json"
    if not result_file.exists():
        # Try case-insensitive search
        matches = [f for f in rd.glob("*.json") if f.stem.upper() == task_id.upper()]
        if matches:
            result_file = matches[0]
        else:
            console.print(f"[bold red]No results found for task [bold]{task_id}[/bold].[/bold red]")
            console.print(f"[dim]Looked in: {rd}[/dim]")
            raise SystemExit(1)

    data = json.loads(result_file.read_text(encoding="utf-8"))
    task_id_display = data.get("task_id", task_id)
    l1 = data.get("layer1", {})
    overall_score = l1.get("score", 0)
    checks = l1.get("checks", [])

    # Header panel
    status_color = "green" if overall_score >= 70 else ("yellow" if overall_score >= 40 else "red")
    console.print(
        Panel(
            f"[bold]Task:[/bold] {task_id_display}\n"
            f"[bold]Category:[/bold] {data.get('category', 'unknown')}\n"
            f"[bold]Level:[/bold] {data.get('level', '?')}\n"
            f"[bold]L1 Score:[/bold] [{status_color}]{overall_score:.0f} / 100[/{status_color}]",
            title="[bold #7F77DD]Legit — Task Detail[/bold #7F77DD]",
            border_style="#7F77DD",
        )
    )

    # Checks table
    table = Table(title="Layer 1 Checks", border_style="#7F77DD")
    table.add_column("Check", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Status")
    table.add_column("Detail")

    for check in checks:
        name = check.get("name", "")
        score = check.get("score", 0)
        weight = check.get("weight", 0)
        detail = check.get("detail", "")
        passed = score >= 70
        status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
        table.add_row(name, f"{score:.0f}", f"{weight:.1f}", status, detail)

    console.print(table)

    # Improvement hints for failed checks
    failed = [c for c in checks if c.get("score", 0) < 70]
    if failed:
        console.print()
        console.print("[bold #7F77DD]Improvement Hints:[/bold #7F77DD]")
        for check in failed:
            name = check.get("name", "")
            hint = HINT_MAP.get(name, "Review the task requirements.")
            console.print(f"  [yellow]>[/yellow] [bold]{name}[/bold]: {hint}")

    # Metadata
    meta = data.get("agent_metadata", {})
    if meta:
        console.print()
        console.print(
            f"[dim]Duration: {meta.get('duration_seconds', '?')}s | "
            f"Steps: {meta.get('steps_taken', '?')} | "
            f"Tools: {', '.join(meta.get('tools_used', [])) or 'none'} | "
            f"Errors: {meta.get('error_count', '?')}[/dim]"
        )
