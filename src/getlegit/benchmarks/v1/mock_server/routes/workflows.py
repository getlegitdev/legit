"""Route handlers for /api/workflow endpoints."""

import json
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

# Track active workflows and their status check counts.
# Key: workflow_id, Value: {"config": dict, "checks": int}
_active_workflows: dict[str, dict] = {}


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def handle_start_workflow(body: dict) -> tuple[int, dict]:
    """POST /api/workflow/start - start a new workflow.

    The workflow_type in the body determines which fixture config is used.
    Returns the workflow ID and initial status.
    """
    workflow_type = body.get("workflow_type", "data_processing")
    workflows = load_fixture("workflows.json")

    config = workflows.get(workflow_type)
    if config is None:
        return 400, {"error": f"Unknown workflow type: {workflow_type}"}

    workflow_id = config["workflow_id"]
    _active_workflows[workflow_id] = {
        "config": config,
        "checks": 0,
        "input": body.get("input", {}),
    }

    return 202, {
        "workflow_id": workflow_id,
        "status": "started",
        "message": f"Workflow '{workflow_type}' started successfully",
    }


def handle_get_workflow_status(workflow_id: str) -> tuple[int, dict]:
    """GET /api/workflow/{id}/status - get workflow status.

    The workflow progresses through its steps on each status check:
    - Check 1: step 1 completed, overall status 'running'
    - Check 2: step 2 completed, overall status 'running'
    - Check 3+: all steps completed, overall status 'completed'
    """
    workflow = _active_workflows.get(workflow_id)
    if workflow is None:
        return 404, {"error": f"Workflow not found: {workflow_id}"}

    workflow["checks"] += 1
    checks = workflow["checks"]
    config = workflow["config"]
    steps = config["steps"]
    total_steps = len(steps)

    # Determine how many steps are completed based on check count.
    completed_count = min(checks, total_steps)
    is_done = completed_count >= total_steps

    step_results = []
    for i, step in enumerate(steps):
        if i < completed_count:
            step_results.append({
                "step_name": step["step_name"],
                "status": "completed",
                "output": step["output"],
            })
        else:
            step_results.append({
                "step_name": step["step_name"],
                "status": "pending",
                "output": None,
            })

    response = {
        "workflow_id": workflow_id,
        "status": "completed" if is_done else "running",
        "steps_completed": completed_count,
        "total_steps": total_steps,
        "step_results": step_results,
    }

    if is_done:
        response["workflow_output"] = config["workflow_output"]

    return 200, response


def reset():
    """Reset active workflows (useful for testing)."""
    _active_workflows.clear()
