"""legit submit — authenticate, score, and upload benchmark results."""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import httpx
from rich.console import Console
from rich.panel import Panel

from getlegit.cli.config import load_config, results_dir

console = Console()

THEME = "#7F77DD"

# GitHub OAuth device flow settings.
GITHUB_CLIENT_ID = "Ov23liEkoIuaMwKDEp6V"
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"

# Legit API endpoint
LEGIT_API_URL = "https://getlegit.dev/api/submit"

# Local token cache
TOKEN_CACHE = Path.home() / ".legit" / "github_token.json"


# ---------------------------------------------------------------------------
# GitHub device-flow OAuth
# ---------------------------------------------------------------------------


def _load_cached_token() -> str | None:
    """Return a cached GitHub token if still valid."""
    if not TOKEN_CACHE.exists():
        return None
    try:
        data = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
        token = data.get("access_token", "")
        if not token:
            return None
        # Quick validation
        resp = httpx.get(
            GITHUB_USER_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "legit-cli",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return token
    except Exception:
        pass
    return None


def _save_token(token: str) -> None:
    TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    TOKEN_CACHE.write_text(
        json.dumps({"access_token": token, "saved_at": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    TOKEN_CACHE.chmod(0o600)


def _github_device_flow() -> str:
    """Run the GitHub device-flow OAuth and return an access token."""
    # Step 1: request device + user codes
    resp = httpx.post(
        GITHUB_DEVICE_CODE_URL,
        headers={"Accept": "application/json"},
        data={"client_id": GITHUB_CLIENT_ID, "scope": "read:user"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    device_code = data["device_code"]
    user_code = data["user_code"]
    verification_uri = data["verification_uri"]
    interval = data.get("interval", 5)
    expires_in = data.get("expires_in", 900)

    console.print(f"\n  Open [bold]{verification_uri}[/bold] in your browser")
    console.print(f"  Enter code: [bold yellow]{user_code}[/bold yellow]\n")

    # Step 2: poll for the token
    deadline = time.monotonic() + expires_in
    while time.monotonic() < deadline:
        time.sleep(interval)
        token_resp = httpx.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
            timeout=15,
        )
        token_data = token_resp.json()
        error = token_data.get("error")

        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval = token_data.get("interval", interval + 5)
            continue
        if error == "expired_token":
            raise click.ClickException("Device code expired. Please try again.")
        if error:
            raise click.ClickException(f"GitHub OAuth error: {error}")

        access_token = token_data.get("access_token")
        if access_token:
            return access_token

    raise click.ClickException("Timed out waiting for GitHub authorization.")


def _get_github_user(token: str) -> dict[str, Any]:
    """Fetch the authenticated GitHub user."""
    resp = httpx.get(
        GITHUB_USER_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "legit-cli",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Local results loading
# ---------------------------------------------------------------------------


def _load_local_results(rd: Path) -> dict[str, Any]:
    """Load the summary and per-task results from .legit/results/."""
    summary_path = rd / "_summary.json"
    if not summary_path.exists():
        raise click.ClickException(
            f"No results found at {rd}. Run [bold]legit run v1 --local[/bold] first."
        )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    tasks: list[dict[str, Any]] = []
    for f in sorted(rd.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            tasks.append(json.loads(f.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass

    return {"summary": summary, "tasks": tasks}


# ---------------------------------------------------------------------------
# Layer 2 local scoring
# ---------------------------------------------------------------------------


def _available_models() -> list[str]:
    """Return the list of Layer 2 model identifiers with configured API keys."""
    from getlegit.judges.layer2.judge import MODEL_CLAUDE, MODEL_GPT4O, MODEL_GEMINI

    models: list[str] = []
    if os.environ.get("ANTHROPIC_API_KEY"):
        models.append(MODEL_CLAUDE)
    if os.environ.get("OPENAI_API_KEY"):
        models.append(MODEL_GPT4O)
    if os.environ.get("GOOGLE_API_KEY"):
        models.append(MODEL_GEMINI)
    return models


async def _run_layer2_single_task(
    task: dict[str, Any],
    models: list[str],
) -> dict[str, Any]:
    """Run Layer 2 evaluation for one task using the available models."""
    from getlegit.judges.layer2.judge import evaluate_with_model
    from getlegit.judges.layer2.aggregate import aggregate_scores

    # Reconstruct a minimal task def and agent output from saved result
    task_def = {
        "task_id": task.get("task_id"),
        "category": task.get("category", "research"),
        "level": task.get("level", 1),
    }
    agent_output = task.get("agent_response") or task.get("agent_output") or {}

    coros = [evaluate_with_model(m, task_def, agent_output) for m in models]
    model_results = await asyncio.gather(*coros, return_exceptions=True)
    model_results = [r if not isinstance(r, Exception) else {"model": "?", "scores": None, "error": str(r)} for r in model_results]

    aggregated = aggregate_scores(model_results)
    return {
        "task_id": task.get("task_id"),
        "model_results": model_results,
        "aggregated": aggregated,
    }


def _estimate_cost(tasks: list[dict[str, Any]], models: list[str]) -> dict[str, Any]:
    """Rough cost estimate based on token counts."""
    from getlegit.judges.layer2.judge import MODEL_CLAUDE, MODEL_GPT4O, MODEL_GEMINI

    # Approximate tokens per task (input ~800, output ~300)
    est_input_tokens = 800 * len(tasks)
    est_output_tokens = 300 * len(tasks)

    rates = {
        MODEL_CLAUDE: {"input": 3.0, "output": 15.0},
        MODEL_GPT4O: {"input": 2.50, "output": 10.0},
        MODEL_GEMINI: {"input": 1.25, "output": 5.0},
    }

    per_model: dict[str, float] = {}
    total = 0.0
    for m in models:
        r = rates.get(m, {"input": 2.0, "output": 8.0})
        cost = (est_input_tokens * r["input"] + est_output_tokens * r["output"]) / 1_000_000
        per_model[m] = round(cost, 4)
        total += cost

    return {
        "models": per_model,
        "total": round(total, 4),
        "est_input_tokens": est_input_tokens,
        "est_output_tokens": est_output_tokens,
    }


def _log_costs(cost_data: dict[str, Any]) -> None:
    """Append cost entry to .legit/costs.json."""
    cost_file = Path.cwd() / ".legit" / "costs.json"
    cost_file.parent.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    if cost_file.exists():
        try:
            entries = json.loads(cost_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, TypeError):
            entries = []

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **cost_data,
    }
    entries.append(entry)
    cost_file.write_text(json.dumps(entries, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Submission to API
# ---------------------------------------------------------------------------


def _submit_to_api(
    github_token: str,
    agent_name: str,
    benchmark_version: str,
    results: dict[str, Any],
) -> dict[str, Any]:
    """POST results to the Legit API endpoint. Returns the API response."""
    payload = {
        "agent_name": agent_name,
        "benchmark_version": benchmark_version,
        "results": results,
        "github_token": github_token,
    }
    try:
        resp = httpx.post(LEGIT_API_URL, json=payload, timeout=30, follow_redirects=True)
    except Exception as exc:
        raise click.ClickException(f"Network error: {exc}")

    # Handle empty or non-JSON responses
    if not resp.text.strip():
        raise click.ClickException(f"Empty response from API (HTTP {resp.status_code})")

    try:
        resp_data = resp.json()
    except Exception:
        raise click.ClickException(f"Invalid API response (HTTP {resp.status_code}): {resp.text[:200]}")

    if resp.status_code == 429:
        raise click.ClickException(
            f"Monthly submit quota exceeded ({resp_data.get('used', '?')}/{resp_data.get('limit', '?')}). "
            f"Plan: {resp_data.get('plan', 'Free')}. "
            f"Resets: {resp_data.get('resets_at', 'next month')}.\n"
            f"  Contribute to getlegit to increase your limit: "
            f"https://github.com/getlegitdev/legit"
        )

    if resp.status_code == 401:
        raise click.ClickException("GitHub authentication failed. Please try again.")

    if resp.status_code >= 400:
        detail = resp_data.get("error", resp.text[:200])
        raise click.ClickException(f"Submit failed: {detail}")

    return resp_data


# ---------------------------------------------------------------------------
# CLI command
# ---------------------------------------------------------------------------


@click.command("submit")
@click.option("--skip-l2", is_flag=True, default=False, help="Skip Layer 2 scoring even if API keys are set.")
@click.option("--scores-only", is_flag=True, default=False, help="Submit only scores and metadata, not raw agent outputs.")
def submit_command(skip_l2: bool, scores_only: bool) -> None:
    """Submit benchmark results for full evaluation and leaderboard ranking."""
    # 1. Load config and results
    try:
        config = load_config()
    except FileNotFoundError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise SystemExit(1)

    rd = results_dir(config)
    local_results = _load_local_results(rd)
    summary = local_results["summary"]
    tasks = local_results["tasks"]

    agent_name = summary.get("agent_name", config.agent.name)
    benchmark_version = summary.get("version", config.benchmark.version)
    l1_score = summary.get("total_score", 0.0)
    task_count = len(tasks)

    console.print()

    # 2. GitHub authentication
    with console.status(f"[{THEME}]Authenticating with GitHub...[/{THEME}]"):
        token = _load_cached_token()

    if token:
        user = _get_github_user(token)
        username = user.get("login", "unknown")
        console.print(f"  Authenticating with GitHub... [green]done[/green] ({username})")
    else:
        console.print(f"  [{THEME}]Authenticating with GitHub...[/{THEME}]")
        token = _github_device_flow()
        _save_token(token)
        user = _get_github_user(token)
        username = user.get("login", "unknown")
        console.print(f"  Authenticated as [bold]{username}[/bold] [green]done[/green]")

    # Prepend GitHub username to agent_name for ownership validation
    agent_name = f"{username}/{agent_name}"

    # 3. Layer 2 scoring (local)
    models = _available_models()
    l2_results: list[dict[str, Any]] = []
    l2_composite: float | None = None

    if skip_l2 or not models:
        if not models and not skip_l2:
            console.print(
                f"\n  [{THEME}]Layer 2 evaluation skipped[/{THEME}] (no API keys configured)"
            )
            console.print(
                "  Set ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY to enable\n"
            )
        else:
            console.print(f"\n  [{THEME}]Layer 2 evaluation skipped[/{THEME}] (--skip-l2)\n")
    else:
        model_count = len(models)
        method = (
            f"median of {model_count} models"
            if model_count > 1
            else "single model"
        )
        console.print(f"\n  Running Layer 2 evaluation ({method})...")

        async def _run_all_l2() -> list[dict[str, Any]]:
            results_list: list[dict[str, Any]] = []
            for task in tasks:
                r = await _run_layer2_single_task(task, models)
                results_list.append(r)
            return results_list

        from getlegit.judges.layer2.judge import MODEL_CLAUDE, MODEL_GPT4O, MODEL_GEMINI

        model_labels = {
            MODEL_CLAUDE: "Claude Sonnet",
            MODEL_GPT4O: "GPT-4o",
            MODEL_GEMINI: "Gemini 2.0 Flash",
        }

        # Show which models are being used
        for i, m in enumerate(models):
            prefix = "  |--" if i < len(models) - 1 else "  `--"
            label = model_labels.get(m, m)
            console.print(f"{prefix} {label}... [dim]queued[/dim]")

        # Run all L2 evaluations
        with console.status(f"  [{THEME}]Scoring with {model_count} model(s)...[/{THEME}]"):
            l2_results = asyncio.run(_run_all_l2())

        # Show completion
        scored_count = sum(
            1 for r in l2_results
            if r.get("aggregated", {}).get("model_count", 0) > 0
        )

        # Overwrite the model lines with results
        for i, m in enumerate(models):
            prefix = "  |--" if i < len(models) - 1 else "  `--"
            label = model_labels.get(m, m)
            console.print(f"{prefix} {label}... [green]done[/green] ({scored_count} tasks scored)")

        # Aggregate overall L2 composite
        composites = [
            r["aggregated"]["composite"]
            for r in l2_results
            if r.get("aggregated", {}).get("composite", 0) > 0
        ]
        if composites:
            l2_composite = round(sum(composites) / len(composites), 1)

        console.print(f"\n  Aggregating scores ({method})... [green]done[/green]")

        # Cost tracking
        cost_data = _estimate_cost(tasks, models)
        _log_costs(cost_data)

    # 4. Combine L1 + L2 for display
    if l2_composite is not None:
        from getlegit.judges.scoring import DEFAULT_L1_WEIGHT, DEFAULT_L2_WEIGHT

        combined_score = round(
            l1_score * DEFAULT_L1_WEIGHT + l2_composite * DEFAULT_L2_WEIGHT, 1
        )
        delta = round(combined_score - l1_score, 1)
        delta_str = f"+{delta}" if delta >= 0 else str(delta)
    else:
        combined_score = l1_score
        delta_str = ""

    # Build results payload for the API
    submission_results = {
        "summary": summary,
        "tasks": tasks,
        "layer2": l2_results if l2_results else None,
        "l2_composite": l2_composite,
        "combined_score": combined_score,
    }

    # Strip raw agent outputs if --scores-only is set
    if scores_only:
        console.print("  Submitting scores only (agent outputs excluded for privacy)")
        for task in submission_results["tasks"]:
            task.pop("agent_response", None)
            task.pop("agent_output", None)

    # 5. Upload to API
    console.print("  Uploading results... ", end="")
    try:
        api_resp = _submit_to_api(github_token=token, agent_name=agent_name, benchmark_version=benchmark_version, results=submission_results)
        console.print("[green]done[/green]")
        run_id = api_resp.get("run_id", "")
    except click.ClickException:
        raise
    except Exception as exc:
        console.print(f"[yellow]failed[/yellow] ({exc})")
        console.print(
            "  [dim]Results saved locally. You can retry with [bold]legit submit[/bold].[/dim]"
        )
        run_id = ""

    # 6. Display final results
    _display_submit_results(
        agent_name=agent_name,
        username=username,
        l1_score=l1_score,
        combined_score=combined_score,
        l2_composite=l2_composite,
        delta_str=delta_str,
        task_count=task_count,
        run_id=run_id,
    )


def _tier_from_score(score: float) -> str:
    """Map a 0-100 score to a tier label."""
    if score >= 90:
        return "Platinum"
    if score >= 75:
        return "Gold"
    if score >= 60:
        return "Silver"
    if score >= 40:
        return "Bronze"
    return "Unranked"


def _display_submit_results(
    *,
    agent_name: str,
    username: str,
    l1_score: float,
    combined_score: float,
    l2_composite: float | None,
    delta_str: str,
    task_count: int,
    run_id: str,
) -> None:
    """Print the final results panel."""
    import webbrowser

    tier = _tier_from_score(combined_score)
    agent_slug = agent_name.lower().replace(" ", "-")
    results_url = f"https://getlegit.dev/agent/{agent_slug}"

    lines: list[str] = []

    if l2_composite is not None:
        lines.append(f"  Legit Score: {l1_score:.0f} -> {combined_score:.0f} ({delta_str} from Layer 2)")
        old_tier = _tier_from_score(l1_score)
        if old_tier != tier:
            lines.append(f"  Tier: {old_tier} -> {tier}")
        else:
            lines.append(f"  Tier: {tier}")
    else:
        lines.append(f"  Layer 1 Score: {l1_score:.0f}/100 (partial)")
        lines.append(f"  Tier: {tier} (estimated)")

    lines.append(f"  Tasks: {task_count}")
    lines.append("")
    lines.append(f"  -> View results: {results_url}")

    body = "\n".join(lines)

    console.print()
    console.print(
        Panel(
            body,
            title=f"[bold {THEME}]Submitted[/bold {THEME}]",
            border_style=THEME,
            width=60,
        )
    )
    console.print()

    # Auto-open the agent's score card in the browser
    card_url = f"https://getlegit.dev/agent/{agent_slug}"
    try:
        webbrowser.open(card_url)
    except Exception:
        pass
