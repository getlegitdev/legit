"""Layer 1 verification entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from getlegit.judges.layer1.checkers import (
    check_code_parses,
    check_keyword_present,
    check_min_count,
    check_numeric_accuracy,
    check_required_fields,
    check_schema_valid,
    check_time,
)


def _load_ground_truth(task_dir: Path | None, variant_id: str | None = None) -> dict[str, Any]:
    """Load ground truth from the task directory for a specific variant.

    Ground truth files live at ``task_dir/ground_truth/{variant_id}.json``.
    Falls back to the legacy ``task_dir/ground_truth.json`` if the per-variant
    file does not exist.
    """
    if task_dir is None:
        return {}

    # Primary: per-variant ground truth
    if variant_id:
        gt_path = task_dir / "ground_truth" / f"{variant_id}.json"
        if gt_path.exists():
            try:
                return json.loads(gt_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}

    # Fallback: legacy single-file ground truth
    gt_path = task_dir / "ground_truth.json"
    if gt_path.exists():
        try:
            return json.loads(gt_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def verify_task(
    task_def: dict[str, Any],
    agent_output: dict[str, Any],
    agent_metadata: dict[str, Any],
    task_dir: Path | None = None,
    variant_id: str | None = None,
) -> dict[str, Any]:
    """
    Run all Layer 1 checks against an agent's output for a given task.

    Returns a dict with:
        - score: float (0-100)
        - checks: list of check result dicts
    """
    output_schema = task_def.get("output_schema", {})
    time_limit = task_def.get("time_limit_seconds", 600)
    code_field = task_def.get("code_field", "code")
    category = task_def.get("category", "").lower()
    tolerance = task_def.get("numeric_tolerance", 0.05)

    # Load variant-specific ground truth
    ground_truth = _load_ground_truth(task_dir, variant_id)
    # Also allow inline ground_truth in task_def
    if not ground_truth and "ground_truth" in task_def:
        ground_truth = task_def["ground_truth"]

    # Extract check parameters from ground truth (primary) with task_def fallback
    keywords = ground_truth.get("keywords", task_def.get("keywords", []))
    numeric_values = ground_truth.get("numeric_values", {})
    min_counts = ground_truth.get("min_counts", task_def.get("min_counts", {}))
    required_fields = task_def.get("required_fields", [])

    duration = agent_metadata.get("duration_seconds", 0)

    # Build a weight map and parameter overrides from layer1_checks if present
    layer1_checks_cfg = task_def.get("layer1_checks", [])
    check_weight_map: dict[str, float] = {}
    check_params: dict[str, dict[str, Any]] = {}
    for cfg in layer1_checks_cfg:
        ctype = cfg.get("type", "")
        check_weight_map[ctype] = cfg.get("weight", 1.0)
        check_params[ctype] = cfg

    # Override parameters from layer1_checks config when present
    if "required_fields" in check_params:
        cfg_fields = check_params["required_fields"].get("fields", None)
        if cfg_fields is not None:
            required_fields = cfg_fields
    if "min_count" in check_params:
        cfg_field = check_params["min_count"].get("field")
        cfg_min = check_params["min_count"].get("min")
        if cfg_field is not None and cfg_min is not None and not min_counts:
            min_counts = {cfg_field: cfg_min}
    if "keyword_present" in check_params:
        cfg_keywords = check_params["keyword_present"].get("keywords", None)
        if cfg_keywords is not None and not keywords:
            keywords = cfg_keywords

    # Run all checks
    checks: list[dict[str, Any]] = []

    result = check_schema_valid(agent_output, output_schema)
    if "schema_valid" in check_weight_map:
        result["weight"] = check_weight_map["schema_valid"]
    checks.append(result)

    result = check_required_fields(agent_output, required_fields)
    if "required_fields" in check_weight_map:
        result["weight"] = check_weight_map["required_fields"]
    checks.append(result)

    result = check_min_count(agent_output, min_counts)
    if "min_count" in check_weight_map:
        result["weight"] = check_weight_map["min_count"]
    checks.append(result)

    # For numeric accuracy, use numeric_values from ground truth
    result = check_numeric_accuracy(agent_output, numeric_values, tolerance)
    if "numeric_accuracy" in check_weight_map:
        result["weight"] = check_weight_map["numeric_accuracy"]
    checks.append(result)

    # Only run code check for Code category or if code_field is present in output
    if category == "code" or code_field in agent_output:
        result = check_code_parses(agent_output, code_field)
        if "code_parses" in check_weight_map:
            result["weight"] = check_weight_map["code_parses"]
        checks.append(result)

    result = check_time(duration, time_limit)
    if "time_check" in check_weight_map:
        result["weight"] = check_weight_map["time_check"]
    checks.append(result)

    result = check_keyword_present(agent_output, keywords)
    if "keyword_present" in check_weight_map:
        result["weight"] = check_weight_map["keyword_present"]
    checks.append(result)

    # Calculate weighted average score
    total_weighted = 0.0
    total_weight = 0.0
    for check in checks:
        w = check.get("weight", 1.0)
        s = check.get("score", 0)
        total_weighted += s * w
        total_weight += w

    final_score = round(total_weighted / total_weight, 1) if total_weight > 0 else 0.0

    return {
        "score": final_score,
        "checks": checks,
    }
