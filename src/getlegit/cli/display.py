"""Rich terminal output for Legit results."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from getlegit.cli.config import LegitConfig

console = Console()

THEME_COLOR = "#7F77DD"
BAR_WIDTH = 10

CATEGORY_ORDER = ["Research", "Extract", "Analyze", "Code", "Write", "Operate"]

TIER_THRESHOLDS = [
    (90, "Platinum", "Top 3%", "#b0b0b0"),
    (75, "Gold", "Top 15%", "#daa520"),
    (60, "Silver", "Top 40%", "#8a8a8a"),
    (40, "Bronze", "Top 70%", "#cd7f32"),
    (0, "Unranked", "", "#9d9d9d"),
]

TIER_SYMBOLS = {
    "Platinum": "\u25c6",  # diamond
    "Gold": "\u25c6",
    "Silver": "\u25c6",
    "Bronze": "\u25c6",
    "Unranked": "\u25c6",
}


def _get_tier(score: float) -> tuple[str, str, str]:
    """Return (tier_name, percentile_label, color) for a given score."""
    for threshold, name, percentile, color in TIER_THRESHOLDS:
        if score >= threshold:
            return name, percentile, color
    return "Unranked", "", "#9d9d9d"


def _score_bar(score: float, width: int = BAR_WIDTH) -> str:
    """Create a text-based bar from a 0-100 score."""
    filled = round(score / 100 * width)
    empty = width - filled
    return f"[bold {THEME_COLOR}]{'█' * filled}[/bold {THEME_COLOR}][dim]{'░' * empty}[/dim]"


def _header_art() -> str:
    """Return a compact Legit ASCII header."""
    return (
        f"[bold {THEME_COLOR}]  ▪ LEGIT[/bold {THEME_COLOR}] "
        f"[dim]— The trust layer for AI agents[/dim]"
    )


def display_results(results: "BenchmarkResults", config: LegitConfig) -> None:  # noqa: F821
    """Display benchmark results in a styled rich panel."""

    total = results.total_score
    tier_name, tier_percentile, tier_color = _get_tier(total)
    tier_symbol = TIER_SYMBOLS.get(tier_name, "\u25c6")

    # Build category lines
    cat_lines: list[str] = []
    for cat in CATEGORY_ORDER:
        # Case-insensitive lookup
        score = None
        for k, v in results.category_scores.items():
            if k.lower() == cat.lower():
                score = v
                break
        if score is not None:
            bar = _score_bar(score)
            cat_lines.append(f"  {cat:<10} {bar}  {score:.0f}")

    # Also show any categories not in the standard order
    shown = {c.lower() for c in CATEGORY_ORDER}
    for k, v in sorted(results.category_scores.items()):
        if k.lower() not in shown:
            bar = _score_bar(v)
            cat_lines.append(f"  {k:<10} {bar}  {v:.0f}")

    categories_text = "\n".join(cat_lines) if cat_lines else "  [dim]No category data[/dim]"

    task_count = len(results.tasks)
    duration = round(results.total_duration)

    # Determine agent name for share link
    agent_slug = getattr(config.agent, "name", "agent") or "agent"
    agent_slug = agent_slug.lower().replace(" ", "-")

    body = (
        f"\n            [bold white]{total:.0f} / 100[/bold white]\n"
        f"            [{tier_color}]{tier_symbol} {tier_name}[/{tier_color}]"
        f" [dim]— {tier_percentile}[/dim]\n"
        f"\n{categories_text}\n"
        f"\n  [dim]{task_count} tasks · {results.failed_count} failed · {duration}s total[/dim]\n"
        f"\n  [dim]→[/dim] [bold]legit submit[/bold] [dim]for full evaluation[/dim]"
        f"\n  [dim]→[/dim] Share: [{THEME_COLOR}]getlegit.dev/card/{agent_slug}[/{THEME_COLOR}]"
        f"\n  [dim]→[/dim] [dim]github.com/getlegitdev/legit[/dim]"
    )

    console.print()
    console.print(f"  {_header_art()}")
    console.print(
        Panel(
            body,
            title=f"[bold {THEME_COLOR}]Legit Score (Layer 1)[/bold {THEME_COLOR}]",
            border_style=THEME_COLOR,
            width=52,
        )
    )
    console.print()
