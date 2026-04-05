"""Layer 1 category checkers — deterministic, automated scoring."""

from __future__ import annotations

import ast
from typing import Any

import jsonschema


def check_schema_valid(
    agent_output: dict[str, Any],
    output_schema: dict[str, Any],
) -> dict[str, Any]:
    """Validate agent output against the task's JSON schema."""
    if not output_schema:
        return {"name": "schema_valid", "score": 100, "weight": 2.0, "detail": "No schema defined."}

    try:
        jsonschema.validate(instance=agent_output, schema=output_schema)
        return {
            "name": "schema_valid",
            "score": 100,
            "weight": 2.0,
            "detail": "Output matches schema.",
        }
    except jsonschema.ValidationError as exc:
        return {
            "name": "schema_valid",
            "score": 0,
            "weight": 2.0,
            "detail": f"Schema violation: {exc.message[:120]}",
        }
    except jsonschema.SchemaError as exc:
        return {
            "name": "schema_valid",
            "score": 50,
            "weight": 2.0,
            "detail": f"Invalid schema definition: {exc.message[:120]}",
        }


def check_required_fields(
    agent_output: dict[str, Any],
    required_fields: list[str],
) -> dict[str, Any]:
    """Check that required fields exist and are non-empty."""
    if not required_fields:
        return {
            "name": "required_fields",
            "score": 100,
            "weight": 2.0,
            "detail": "No required fields specified.",
        }

    present = 0
    missing: list[str] = []
    for field_name in required_fields:
        value = agent_output.get(field_name)
        if value is not None and value != "" and value != [] and value != {}:
            present += 1
        else:
            missing.append(field_name)

    score = round(present / len(required_fields) * 100) if required_fields else 100
    detail = "All required fields present." if not missing else f"Missing: {', '.join(missing)}"
    return {"name": "required_fields", "score": score, "weight": 2.0, "detail": detail}


def check_min_count(
    agent_output: dict[str, Any],
    min_counts: dict[str, int],
) -> dict[str, Any]:
    """Check that array fields meet minimum count requirements."""
    if not min_counts:
        return {
            "name": "min_count",
            "score": 100,
            "weight": 1.0,
            "detail": "No minimum counts specified.",
        }

    passed = 0
    failed_fields: list[str] = []
    for field_name, min_val in min_counts.items():
        value = agent_output.get(field_name, [])
        if isinstance(value, (list, tuple)) and len(value) >= min_val:
            passed += 1
        elif isinstance(value, (int, float)) and value >= min_val:
            passed += 1
        else:
            actual = len(value) if isinstance(value, (list, tuple)) else value
            failed_fields.append(f"{field_name} (need {min_val}, got {actual})")

    total = len(min_counts)
    score = round(passed / total * 100) if total else 100
    detail = (
        "All counts met."
        if not failed_fields
        else f"Below minimum: {'; '.join(failed_fields)}"
    )
    return {"name": "min_count", "score": score, "weight": 1.0, "detail": detail}


def check_numeric_accuracy(
    agent_output: dict[str, Any],
    ground_truth: dict[str, Any],
    tolerance: float = 0.05,
) -> dict[str, Any]:
    """Check numeric values against ground truth within tolerance."""
    numeric_truth = {
        k: v for k, v in ground_truth.items() if isinstance(v, (int, float))
    }
    if not numeric_truth:
        return {
            "name": "numeric_accuracy",
            "score": 100,
            "weight": 1.5,
            "detail": "No numeric ground truth.",
        }

    correct = 0
    wrong: list[str] = []
    for key, expected in numeric_truth.items():
        actual = agent_output.get(key)
        if actual is None:
            wrong.append(f"{key} (missing)")
            continue
        try:
            actual_f = float(actual)
            expected_f = float(expected)
            if expected_f == 0:
                if actual_f == 0:
                    correct += 1
                else:
                    wrong.append(f"{key} (expected 0, got {actual_f})")
            elif abs(actual_f - expected_f) / abs(expected_f) <= tolerance:
                correct += 1
            else:
                wrong.append(f"{key} (expected ~{expected_f}, got {actual_f})")
        except (ValueError, TypeError):
            wrong.append(f"{key} (non-numeric: {actual!r})")

    total = len(numeric_truth)
    score = round(correct / total * 100) if total else 100
    detail = "All numeric values within tolerance." if not wrong else f"Off: {'; '.join(wrong)}"
    return {"name": "numeric_accuracy", "score": score, "weight": 1.5, "detail": detail}


def check_code_parses(
    agent_output: dict[str, Any],
    code_field: str = "code",
) -> dict[str, Any]:
    """Check if the output code parses as valid Python (AST check, does not execute)."""
    code = agent_output.get(code_field)
    if code is None:
        # Not a code task or no code field
        return {
            "name": "code_parses",
            "score": 100,
            "weight": 1.5,
            "detail": "No code field to check.",
        }

    if not isinstance(code, str) or not code.strip():
        return {
            "name": "code_parses",
            "score": 0,
            "weight": 1.5,
            "detail": "Code field is empty.",
        }

    # Try to parse as Python AST
    try:
        ast.parse(code)
        return {
            "name": "code_parses",
            "score": 100,
            "weight": 1.5,
            "detail": "Code parses successfully.",
        }
    except SyntaxError as exc:
        return {
            "name": "code_parses",
            "score": 20,
            "weight": 1.5,
            "detail": f"Syntax error: {exc.msg} (line {exc.lineno})",
        }


def check_time(
    duration_seconds: float,
    time_limit_seconds: float,
) -> dict[str, Any]:
    """Check if the agent responded within the time limit."""
    if time_limit_seconds <= 0:
        return {
            "name": "time_check",
            "score": 100,
            "weight": 0.5,
            "detail": "No time limit.",
        }

    if duration_seconds <= time_limit_seconds:
        # Full score if within limit; bonus flavor if fast
        return {
            "name": "time_check",
            "score": 100,
            "weight": 0.5,
            "detail": f"Completed in {duration_seconds:.0f}s (limit: {time_limit_seconds:.0f}s).",
        }
    else:
        # Partial credit: linear decay up to 2x the limit, then 0
        overage_ratio = duration_seconds / time_limit_seconds
        if overage_ratio <= 2.0:
            score = max(0, round(100 * (2.0 - overage_ratio)))
        else:
            score = 0
        return {
            "name": "time_check",
            "score": score,
            "weight": 0.5,
            "detail": f"Took {duration_seconds:.0f}s (limit: {time_limit_seconds:.0f}s).",
        }


def check_keyword_present(
    agent_output: dict[str, Any],
    keywords: list[str],
) -> dict[str, Any]:
    """Check that certain keywords appear in the agent output."""
    if not keywords:
        return {
            "name": "keyword_present",
            "score": 100,
            "weight": 1.0,
            "detail": "No keywords specified.",
        }

    # Flatten output to text for keyword search
    text = _flatten_to_text(agent_output).lower()

    found = 0
    missing: list[str] = []
    for kw in keywords:
        if kw.lower() in text:
            found += 1
        else:
            missing.append(kw)

    score = round(found / len(keywords) * 100) if keywords else 100
    detail = (
        "All keywords found."
        if not missing
        else f"Missing keywords: {', '.join(missing[:5])}"
    )
    return {"name": "keyword_present", "score": score, "weight": 1.0, "detail": detail}


def _flatten_to_text(obj: Any, depth: int = 0) -> str:
    """Recursively flatten a dict/list to a searchable text string."""
    if depth > 10:
        return str(obj)
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(_flatten_to_text(v, depth + 1) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return " ".join(_flatten_to_text(item, depth + 1) for item in obj)
    return str(obj)
