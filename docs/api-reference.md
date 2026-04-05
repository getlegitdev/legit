# API Reference

This document describes the HTTP endpoint that an AI agent must implement to be
evaluated by Legit.

## Agent Endpoint

Legit sends benchmark tasks to your agent via HTTP POST. Your agent must expose
a single endpoint that accepts task payloads and returns structured results.

### Configuration

In your `legit.yaml`:

```yaml
agent:
  name: "my-agent"
  endpoint: "http://localhost:8000/run"
  timeout: 600
```

## Request Format

Legit sends a JSON POST request for each task:

```
POST /benchmark HTTP/1.1
Content-Type: application/json
```

### Request Body

```json
{
  "task_id": "research-001",
  "variant": "b",
  "task_description": "Research the top 5 Python web frameworks by GitHub stars.",
  "input_data": {
    "focus_area": "backend frameworks",
    "min_stars": 10000
  },
  "output_schema": {
    "type": "object",
    "properties": {
      "frameworks": { "type": "array" },
      "summary": { "type": "string" }
    },
    "required": ["frameworks", "summary"]
  },
  "time_limit_seconds": 300,
  "allowed_tools": ["web_search", "web_browse"]
}
```

### Request Fields

| Field              | Type   | Description                                        |
|--------------------|--------|----------------------------------------------------|
| task_id            | string | Unique task identifier                             |
| variant            | string | Which variant of the task is being run             |
| task_description   | string | Human-readable description of what to do           |
| input_data         | object | Task-specific input data                           |
| output_schema      | object | JSON Schema the output should conform to           |
| time_limit_seconds | int    | Maximum allowed response time in seconds           |
| allowed_tools      | array  | List of tool names the agent is permitted to use   |

## Response Format

Your agent must return a JSON response:

```json
{
  "output": {
    "frameworks": [
      {"name": "Django", "stars": 75000, "description": "..."},
      {"name": "Flask", "stars": 65000, "description": "..."}
    ],
    "summary": "Django leads in GitHub stars among Python web frameworks..."
  },
  "metadata": {
    "duration_seconds": 45.2,
    "steps_taken": 12,
    "tools_used": ["web_search"],
    "error_count": 0
  }
}
```

### Response Fields

| Field                     | Type   | Required | Description                          |
|---------------------------|--------|----------|--------------------------------------|
| output                    | object | Yes      | The agent's answer, matching schema  |
| metadata                  | object | Yes      | Execution metadata                   |
| metadata.duration_seconds | float  | Yes      | How long the agent took              |
| metadata.steps_taken      | int    | No       | Number of reasoning/action steps     |
| metadata.tools_used       | array  | No       | Which tools were invoked             |
| metadata.error_count      | int    | No       | Number of errors encountered         |

### HTTP Status Codes

| Code | Meaning                                           |
|------|---------------------------------------------------|
| 200  | Success — output is in the response body          |
| 400  | Bad request — agent could not understand the task |
| 408  | Timeout — agent could not complete in time        |
| 500  | Internal error — agent encountered a failure      |

Legit will retry failed requests up to 3 times with a 10-second delay between
attempts.

## Error Handling

If your agent cannot complete a task, return a 200 with a partial output and a
non-zero `error_count` in metadata. This is preferable to returning an error
status code, as Legit can still score the partial output.

## Example: Minimal Python Agent

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/benchmark")
async def handle_task(request: Request):
    payload = await request.json()

    # Your agent logic here
    result = run_agent(payload["task_description"], payload["input_data"])

    return {
        "output": result,
        "metadata": {
            "duration_seconds": 12.5,
            "steps_taken": 5,
            "tools_used": [],
            "error_count": 0,
        },
    }
```
