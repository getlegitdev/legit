"""Main CLI entry point for Legit."""

import click

from getlegit import __version__
from getlegit.cli.commands.init_cmd import init_command
from getlegit.cli.commands.run import run_command
from getlegit.cli.commands.explain import explain_command
from getlegit.cli.commands.submit import submit_command
from getlegit.cli.commands.costs import costs_command


@click.group()
@click.version_option(version=__version__, prog_name="legit")
def cli() -> None:
    """Legit — The trust layer for AI agents."""


cli.add_command(init_command, name="init")
cli.add_command(run_command, name="run")
cli.add_command(explain_command, name="explain")
cli.add_command(submit_command, name="submit")
cli.add_command(costs_command, name="costs")
