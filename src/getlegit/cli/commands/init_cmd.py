"""legit init command — create a legit.yaml config file."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

from getlegit.cli.config import create_config

console = Console()


@click.command("init")
@click.option("--agent", required=True, help="Name of the AI agent to evaluate.")
@click.option("--endpoint", required=True, help="HTTP endpoint URL of the agent.")
def init_command(agent: str, endpoint: str) -> None:
    """Initialize a new Legit evaluation config."""
    try:
        config_path = create_config(agent_name=agent, agent_endpoint=endpoint)
        console.print(
            Panel(
                f"[bold green]Created[/bold green] {config_path.name}\n\n"
                f"  Agent:    [bold]{agent}[/bold]\n"
                f"  Endpoint: [bold]{endpoint}[/bold]\n\n"
                f"Next: [dim]legit run v1 --local[/dim]",
                title="[bold #7F77DD]Legit[/bold #7F77DD]",
                border_style="#7F77DD",
            )
        )
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)
