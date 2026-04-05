# Adding a New Benchmark Task

This guide walks you through creating a new benchmark task for Legit.

## Directory Structure

Each task lives in its own directory under
`src/getlegit/benchmarks/<version>/tasks/`:

```
src/getlegit/benchmarks/v1/tasks/
  research-001/
    task.json           # Task definition (required)
    ground_truth.json   # Expected values for deterministic checks (optional)
    variants/
      a.json            # Variant A input data
      b.json            # Variant B input data
      c.json            # Variant C input data
```

## Step 1: Choose a Category and Level

**Categories:** research, extract, analyze, code, write, operate

**Levels:**

| Level | Description                                | Multiplier |
|-------|--------------------------------------------|------------|
| 1     | Basic task, single-step                    | 1.0x       |
| 2     | Intermediate, requires some reasoning      | 1.5x       |
| 3     | Advanced, multi-step or nuanced            | 2.0x       |
| 4     | Expert, requires tool use or deep analysis | 3.0x       |

## Step 2: Create task.json

```json
{
  "task_id": "research-001",
  "category": "research",
  "level": 2,
  "task_description": "Research the top 5 Python web frameworks by GitHub stars and provide a comparison table.",
  "variants": ["a", "b", "c"],
  "output_schema": {
    "type": "object",
    "properties": {
      "frameworks": {
        "type": "array",
        "items": { "type": "object" }
      },
      "summary": { "type": "string" }
    },
    "required": ["frameworks", "summary"]
  },
  "required_fields": ["frameworks", "summary"],
  "min_counts": { "frameworks": 5 },
  "keywords": ["Django", "Flask", "FastAPI"],
  "time_limit_seconds": 300,
  "allowed_tools": ["web_search", "web_browse"]
}
```

### Field Reference

| Field                | Type     | Required | Description                                   |
|----------------------|----------|----------|-----------------------------------------------|
| task_id              | string   | Yes      | Unique identifier (category-NNN)              |
| category             | string   | Yes      | One of the six categories                     |
| level                | int      | Yes      | Difficulty 1-4                                |
| task_description     | string   | Yes      | What the agent should do                      |
| variants             | string[] | Yes      | List of variant IDs                           |
| output_schema        | object   | No       | JSON Schema for output validation             |
| required_fields      | string[] | No       | Fields that must be non-empty                 |
| min_counts           | object   | No       | Minimum array lengths                         |
| keywords             | string[] | No       | Keywords expected in output                   |
| time_limit_seconds   | int      | No       | Time limit (default: 600)                     |
| allowed_tools        | string[] | No       | Tools the agent may use                       |
| numeric_tolerance    | float    | No       | Tolerance for numeric checks (default: 0.05)  |
| code_field           | string   | No       | Field name containing code (default: "code")  |
| ground_truth         | object   | No       | Inline ground truth (alternative to file)     |

## Step 3: Create Variants

Variants ensure agents cannot memorize answers. Each variant should test the
same skill with different input data.

`variants/a.json`:
```json
{
  "input_data": {
    "focus_area": "backend frameworks",
    "min_stars": 10000
  },
  "task_description": "Research the top 5 Python backend web frameworks by GitHub stars (minimum 10,000 stars)."
}
```

Variant files can override any field from task.json. Commonly overridden:
`input_data`, `task_description`, `keywords`.

## Step 4: Add Ground Truth (Optional)

If your task has verifiable numeric answers, add `ground_truth.json`:

```json
{
  "framework_count": 5,
  "top_framework_stars": 75000
}
```

Layer 1 will check the agent's output against these values within the
configured tolerance.

## Step 5: Test Your Task

Run the benchmark with only your new task's category:

```bash
legit run --categories research
```

Review the results in `.legit/results/` and verify the scoring makes sense.

## Checklist

- [ ] task.json has all required fields
- [ ] At least 3 variants exist
- [ ] Variants test the same skill with different inputs
- [ ] output_schema validates the expected structure
- [ ] required_fields and keywords are appropriate
- [ ] Time limit is reasonable for the task difficulty
- [ ] Ground truth values (if any) are accurate
