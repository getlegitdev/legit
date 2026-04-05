"""Score calculation for Legit benchmarks (Layer 1 + Layer 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from getlegit.cli.runner import BenchmarkResults

LEVEL_MULTIPLIER = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 3.0,
}

# Default weights when combining Layer 1 and Layer 2.
DEFAULT_L1_WEIGHT = 0.6
DEFAULT_L2_WEIGHT = 0.4


def _combine_task_score(
    l1_score: float,
    l2_score: float | None,
    l1_weight: float = DEFAULT_L1_WEIGHT,
    l2_weight: float = DEFAULT_L2_WEIGHT,
) -> tuple[float, str]:
    """
    Combine Layer 1 and Layer 2 scores for a single task.

    Returns:
        (combined_score, note) where *note* is empty when both layers are
        present, or describes a partial-score situation.
    """
    if l2_score is not None:
        combined = l1_score * l1_weight + l2_score * l2_weight
        return round(combined, 1), ""

    # Only L1 available — report partial score.
    return round(l1_score, 1), "L2 unavailable; score is L1-only (partial)"


def calculate_scores(
    results: "BenchmarkResults",
    l1_weight: float = DEFAULT_L1_WEIGHT,
    l2_weight: float = DEFAULT_L2_WEIGHT,
) -> "BenchmarkResults":
    """
    Calculate category and overall scores from individual task results.

    When Layer 2 results are available on a task (``task.layer2`` dict with a
    ``composite`` key), the task score is a weighted combination:

        task_score = L1_score * l1_weight + L2_composite * l2_weight

    When only Layer 1 results exist the task score equals the L1 score and a
    note is attached indicating partial scoring.

    Scoring:
        Task raw = combined_score (L1 or L1+L2)
        Task weighted = raw * level_multiplier
        Category score = sum(weighted) / sum(100 * multipliers) * 100
        Total = equal average of categories that have tasks
    """
    # Group tasks by category
    category_tasks: dict[str, list] = {}
    for task in results.tasks:
        cat = task.category.capitalize()
        if cat not in category_tasks:
            category_tasks[cat] = []
        category_tasks[cat].append(task)

    category_scores: dict[str, float] = {}
    partial_categories: list[str] = []

    for cat, tasks in category_tasks.items():
        weighted_sum = 0.0
        max_sum = 0.0
        has_partial = False

        for task in tasks:
            l1_score = task.layer1.get("score", 0)

            # Retrieve Layer 2 composite if present.
            l2_data = getattr(task, "layer2", None)
            l2_composite: float | None = None
            if isinstance(l2_data, dict):
                l2_composite = l2_data.get("composite")

            # Use per-task weights if available, otherwise fall back to defaults.
            task_l1_w = getattr(task, "layer1_weight", None) or l1_weight
            task_l2_w = getattr(task, "layer2_weight", None) or l2_weight

            combined, note = _combine_task_score(
                l1_score, l2_composite, task_l1_w, task_l2_w
            )
            if note:
                has_partial = True

            multiplier = LEVEL_MULTIPLIER.get(task.level, 1.0)
            weighted_sum += combined * multiplier
            max_sum += 100.0 * multiplier

        if max_sum > 0:
            category_scores[cat] = round(weighted_sum / max_sum * 100, 1)
        else:
            category_scores[cat] = 0.0

        if has_partial:
            partial_categories.append(cat)

    results.category_scores = category_scores

    # Total = equal average of categories
    if category_scores:
        results.total_score = round(
            sum(category_scores.values()) / len(category_scores), 1
        )
    else:
        results.total_score = 0.0

    # Attach metadata about partial scoring.
    if partial_categories:
        results.scoring_notes = (  # type: ignore[attr-defined]
            f"Partial scoring (L1-only) for categories: {', '.join(partial_categories)}"
        )

    return results
