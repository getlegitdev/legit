"""Median aggregation of multi-model Layer 2 scores."""

from __future__ import annotations

import statistics
from typing import Any

SCORE_AXES = ("accuracy", "completeness", "quality", "structure", "extra_axis")

# Standard deviation threshold above which we flag low agreement.
LOW_AGREEMENT_THRESHOLD = 1.5


def aggregate_scores(model_results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aggregate Layer 2 scores from multiple models using the median.

    Args:
        model_results: List of result dicts from ``cross_evaluate``.  Each dict
            has ``model``, ``scores`` (dict or None), and ``error``.

    Returns:
        A dict containing:
        - ``axes``: per-axis aggregated info (median, values, stdev, flagged)
        - ``composite``: the overall L2 score normalized to 0-100
        - ``model_count``: how many models contributed scores
        - ``low_agreement``: list of axis names where stdev > 1.5
        - ``model_details``: summary of per-model availability
    """
    # Collect valid score dicts
    valid_scores: list[dict[str, int]] = []
    model_details: list[dict[str, Any]] = []

    for result in model_results:
        scores = result.get("scores")
        model_details.append({
            "model": result.get("model", "unknown"),
            "available": scores is not None,
            "error": result.get("error"),
        })
        if scores is not None:
            valid_scores.append(scores)

    if not valid_scores:
        return {
            "axes": {},
            "composite": 0.0,
            "model_count": 0,
            "low_agreement": [],
            "model_details": model_details,
        }

    # Aggregate each axis
    axes: dict[str, dict[str, Any]] = {}
    low_agreement: list[str] = []

    for axis in SCORE_AXES:
        values = [s[axis] for s in valid_scores if axis in s]
        if not values:
            axes[axis] = {"median": 0, "values": [], "stdev": 0.0, "flagged": False}
            continue

        median_val = statistics.median(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0.0
        flagged = stdev > LOW_AGREEMENT_THRESHOLD

        if flagged:
            low_agreement.append(axis)

        axes[axis] = {
            "median": median_val,
            "values": values,
            "stdev": round(stdev, 2),
            "flagged": flagged,
        }

    # Composite score: average of medians, normalized from 1-5 scale to 0-100.
    medians = [info["median"] for info in axes.values() if info["median"] > 0]
    if medians:
        avg_median = sum(medians) / len(medians)
        # Map 1-5 to 0-100: (score - 1) / 4 * 100
        composite = round((avg_median - 1) / 4 * 100, 1)
    else:
        composite = 0.0

    return {
        "axes": axes,
        "composite": composite,
        "model_count": len(valid_scores),
        "low_agreement": low_agreement,
        "model_details": model_details,
    }
