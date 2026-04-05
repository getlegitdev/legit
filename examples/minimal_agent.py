"""Minimal Legit-compatible agent example.

Usage:
    pip install fastapi uvicorn
    python examples/minimal_agent.py

Then in another terminal:
    pip install getlegit
    legit init --agent "MinimalBot" --endpoint "http://localhost:8000/run"
    legit run v1 --local
"""

import time
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

app = FastAPI(title="Minimal Legit Agent")


class TaskRequest(BaseModel):
    task_id: str
    variant: str = "a"
    task_description: str = ""
    input_data: dict[str, Any] = {}
    output_schema: dict[str, Any] = {}
    time_limit_seconds: int = 600
    allowed_tools: list[str] = []


# --- Template responses by category prefix ---

def _research_output(req: TaskRequest) -> dict:
    """Return a structured comparison with 5 items."""
    product = req.input_data.get("product", "Unknown")
    return {
        "competitors": [
            {
                "name": f"Competitor {i}",
                "description": f"A competitor to {product} in the market.",
                "strengths": ["Feature A", "Feature B"],
                "weaknesses": ["Limited integrations"],
                "market_position": "challenger",
            }
            for i in range(1, 6)
        ],
        "summary": f"Analysis of 5 competitors for {product}.",
        "methodology": "Web research and feature comparison.",
    }


def _extract_output(req: TaskRequest) -> dict:
    """Return headers + rows table extraction."""
    return {
        "headers": ["Name", "Value", "Category"],
        "rows": [
            ["Item 1", "100", "A"],
            ["Item 2", "200", "B"],
            ["Item 3", "150", "A"],
        ],
        "row_count": 3,
    }


def _analyze_output(req: TaskRequest) -> dict:
    """Return statistics, trends, and insights."""
    return {
        "statistics": {"mean": 150.0, "median": 150.0, "std_dev": 40.8},
        "trends": ["Upward trend in Q1", "Seasonal dip in Q3"],
        "insights": [
            "Primary driver is organic growth.",
            "Cost efficiency improved 12% year-over-year.",
        ],
        "summary": "Data shows positive momentum with seasonal variance.",
    }


def _code_output(req: TaskRequest) -> dict:
    """Return fixed code + bug description."""
    return {
        "fixed_code": "def add(a, b):\n    return a + b\n",
        "bug_description": "The original function used subtraction instead of addition.",
        "changes_made": ["Changed '-' operator to '+' on line 2"],
    }


def _write_output(req: TaskRequest) -> dict:
    """Return title + body + tags."""
    return {
        "title": "Understanding Modern AI Agents",
        "body": (
            "AI agents are autonomous systems that perceive, decide, and act. "
            "This post explores their architecture, evaluation, and trust. "
            "We cover key patterns including tool use, planning, and reflection. "
            "Benchmarking agents — rather than models — is the next frontier."
        ),
        "tags": ["ai", "agents", "benchmarks"],
        "word_count": 42,
    }


def _operate_output(req: TaskRequest) -> dict:
    """Return status_code + response_data for an API operation."""
    return {
        "status_code": 200,
        "response_data": {"id": "op_123", "result": "success"},
        "actions_taken": ["Authenticated", "Sent POST request", "Verified response"],
    }


# Map first character of task_id to handler
_HANDLERS = {
    "R": _research_output,
    "E": _extract_output,
    "A": _analyze_output,
    "C": _code_output,
    "W": _write_output,
    "O": _operate_output,
}


@app.post("/run")
async def run_task(req: TaskRequest) -> dict[str, Any]:
    """Handle a Legit benchmark task request."""
    start = time.time()

    # Pick handler based on task_id prefix (R=research, E=extract, etc.)
    prefix = req.task_id[0].upper() if req.task_id else "R"
    handler = _HANDLERS.get(prefix, _research_output)
    output = handler(req)

    duration = round(time.time() - start, 3)

    return {
        "status": "completed",
        "output": output,
        "metadata": {
            "duration_seconds": duration,
            "steps_taken": 3,
            "tools_used": req.allowed_tools[:1] if req.allowed_tools else [],
            "error_count": 0,
        },
    }


if __name__ == "__main__":
    import uvicorn

    print("Starting minimal Legit agent on http://localhost:8000")
    print("POST /run to handle benchmark tasks")
    uvicorn.run(app, host="0.0.0.0", port=8000)
