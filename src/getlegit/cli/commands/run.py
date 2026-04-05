"""legit run command — execute benchmark tasks against an agent."""

from __future__ import annotations

import click
from rich.console import Console

from getlegit.cli.config import load_config
from getlegit.cli.runner import BenchmarkRunner
from getlegit.cli.display import display_results

console = Console()


@click.command("run")
@click.argument("version", default="v1")
@click.option("--local", is_flag=True, default=False, help="Run evaluation locally.")
def run_command(version: str, local: bool) -> None:
    """Run benchmark tasks against the configured agent."""
    if not local:
        console.print(
            "[bold #7F77DD]Remote evaluation coming soon.[/bold #7F77DD] "
            "Use [bold]--local[/bold] for now."
        )
        return

    try:
        config = load_config()
    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

    runner = BenchmarkRunner(config=config, version=version)
    results = runner.run()
    display_results(results, config)
