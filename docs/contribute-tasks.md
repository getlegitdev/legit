# Contributing Tasks to Legit

Thank you for considering a task contribution. This document explains the task
structure, variant system, and ground truth format.

## Task Structure

A Legit benchmark task is a self-contained unit that tests one specific agent
capability. Every task belongs to exactly one category and has a difficulty
level.

### Categories

| Category | What it tests                              | Example                        |
|----------|--------------------------------------------|--------------------------------|
| Research | Finding and synthesizing information       | Market analysis, fact-finding  |
| Extract  | Pulling structured data from unstructured  | PDF parsing, table extraction  |
| Analyze  | Interpreting data and drawing conclusions  | Trend analysis, risk assessment|
| Code     | Generating or modifying code               | Function implementation, debug |
| Write    | Producing written content                  | Email drafting, report writing |
| Operate  | Executing multi-step operational workflows | Deployment, API integration    |

### Task Definition (task.json)

The `task.json` file is the core of every task. It tells the benchmark runner
what to send to the agent and how to verify the response.

Key fields:

- **task_id**: Unique identifier formatted as `category-NNN` (e.g., `analyze-003`).
- **category**: Must match one of the six categories above.
- **level**: Integer 1-4 indicating difficulty.
- **task_description**: A clear, unambiguous description of what the agent must do.
- **variants**: A list of variant IDs (strings) like `["a", "b", "c"]`.
- **output_schema**: A JSON Schema that the agent's output must conform to.

## The Variant System

Variants prevent agents from memorizing benchmark answers. Each task must have
at least 3 variants. During a benchmark run, one variant is chosen at random.

### How Variants Work

1. The runner loads `task.json` and picks a random variant ID.
2. It loads `variants/<id>.json` from the task directory.
3. Fields in the variant file override the corresponding fields in `task.json`.
4. The merged definition is sent to the agent.

### What to Vary

Good variants change the **input data** while preserving the **skill tested**:

- Different companies, dates, or datasets for research/analysis tasks
- Different code problems of the same type and difficulty
- Different writing contexts with the same structural requirements

Bad variants change the fundamental skill being tested or make the task
trivially easier/harder.

### Variant File Example

```json
{
  "input_data": {
    "company": "Stripe",
    "year": 2024,
    "data_url": "https://example.com/stripe-2024.csv"
  },
  "keywords": ["Stripe", "payments", "revenue"]
}
```

## Ground Truth Format

Ground truth enables deterministic (Layer 1) scoring of factual accuracy.

### ground_truth.json

Place this file alongside `task.json` in the task directory. It contains
key-value pairs of field names and expected values.

```json
{
  "total_revenue": 14000000,
  "employee_count": 8000,
  "founded_year": 2010
}
```

**Numeric values** are compared with a configurable tolerance (default 5%).

**String values** in ground truth are not currently used by Layer 1 checks but
may be used by Layer 2 evaluators as reference material.

### Inline Ground Truth

Alternatively, include ground truth directly in `task.json`:

```json
{
  "task_id": "extract-005",
  "ground_truth": {
    "row_count": 150,
    "column_count": 12
  }
}
```

The inline format is useful for variant-specific ground truth (place it in the
variant JSON file instead).

## Submission Guidelines

1. **One skill per task.** Do not combine research + code in a single task.
2. **At least 3 variants.** More is better, up to 5.
3. **Clear task descriptions.** The agent should understand what to do without
   ambiguity.
4. **Realistic difficulty.** Level 1 should be achievable by most agents; level
   4 should challenge the best.
5. **Appropriate time limits.** Allow enough time for the task but not so much
   that it hides performance differences.
6. **Test your task.** Run it against at least one agent before submitting.
