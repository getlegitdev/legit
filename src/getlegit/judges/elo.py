"""Elo rating math for agent ranking."""

from __future__ import annotations

import math

DEFAULT_RATING = 1000
K_FACTOR = 32


def expected_score(rating_a: float, rating_b: float) -> float:
    """Calculate expected score for player A against player B."""
    return 1.0 / (1.0 + math.pow(10, (rating_b - rating_a) / 400))


def update_rating(
    rating: float,
    actual_score: float,
    expected: float,
    k: float = K_FACTOR,
) -> float:
    """Update an Elo rating given actual vs expected score.

    Args:
        rating: Current Elo rating.
        actual_score: Actual outcome (1.0 for win, 0.5 for draw, 0.0 for loss).
        expected: Expected score from expected_score().
        k: K-factor controlling rating volatility.

    Returns:
        Updated Elo rating.
    """
    return round(rating + k * (actual_score - expected), 1)


def match_result(
    rating_a: float,
    rating_b: float,
    score_a: float,
    score_b: float,
    k: float = K_FACTOR,
) -> tuple[float, float]:
    """Calculate new ratings after a head-to-head comparison.

    Scores are normalized to [0, 1] where higher is better.
    The agent with the higher benchmark score "wins".

    Args:
        rating_a: Current Elo rating for agent A.
        rating_b: Current Elo rating for agent B.
        score_a: Benchmark score for agent A (0-100).
        score_b: Benchmark score for agent B (0-100).
        k: K-factor.

    Returns:
        Tuple of (new_rating_a, new_rating_b).
    """
    # Determine outcome
    if score_a > score_b:
        actual_a, actual_b = 1.0, 0.0
    elif score_b > score_a:
        actual_a, actual_b = 0.0, 1.0
    else:
        actual_a, actual_b = 0.5, 0.5

    exp_a = expected_score(rating_a, rating_b)
    exp_b = expected_score(rating_b, rating_a)

    new_a = update_rating(rating_a, actual_a, exp_a, k)
    new_b = update_rating(rating_b, actual_b, exp_b, k)

    return new_a, new_b


def bulk_update(
    ratings: dict[str, float],
    results: list[tuple[str, str, float, float]],
    k: float = K_FACTOR,
) -> dict[str, float]:
    """Update ratings for multiple pairwise comparisons.

    Args:
        ratings: Dict of agent_name -> current rating.
        results: List of (agent_a, agent_b, score_a, score_b) tuples.
        k: K-factor.

    Returns:
        Updated ratings dict.
    """
    updated = dict(ratings)
    for agent_a, agent_b, score_a, score_b in results:
        ra = updated.get(agent_a, DEFAULT_RATING)
        rb = updated.get(agent_b, DEFAULT_RATING)
        new_a, new_b = match_result(ra, rb, score_a, score_b, k)
        updated[agent_a] = new_a
        updated[agent_b] = new_b
    return updated
