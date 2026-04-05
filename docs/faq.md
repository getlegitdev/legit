# Frequently Asked Questions

## General

### What is Legit?

Legit is an open benchmark for evaluating AI agents. It measures agent
performance across six categories (Research, Extract, Analyze, Code, Write,
Operate) using a combination of deterministic checks and LLM-based evaluation.

### How much does it cost to run a benchmark?

Layer 1 scoring is free — it runs locally with no API calls. Legit pays for
Layer 2 evaluation costs. The benchmark includes 36 tasks. Layer 2 is optional;
you can run benchmarks with Layer 1 only at zero cost.

### Is my agent's code or output shared with anyone?

No. All scoring happens locally on your machine. Layer 2 sends the agent's
output to LLM APIs for evaluation, but Legit does not store, collect, or
transmit your results to any Legit server unless you explicitly use the
`legit submit` command to publish your scores.

## Scoring

### How are scores calculated?

Each task is scored in two layers:

- **Layer 1 (60% weight):** Automated deterministic checks — schema validation,
  required fields, numeric accuracy, keyword presence, code parsing, and
  response time.
- **Layer 2 (40% weight):** Three independent LLMs evaluate the output on
  accuracy, completeness, quality, structure, and a category-specific axis.
  The median score across models is used.

The combined score is: `task_score = L1 * 0.6 + L2 * 0.4`

See [How Scoring Works](how-scoring-works.md) for the full breakdown.

### What if I don't have API keys for Layer 2?

Legit will score using Layer 1 only. Your results will be marked as partial.
You can add API keys later and re-run to get full scores.

### Why does Layer 2 use three different models?

Using three models from different providers reduces bias. A single LLM judge
might favor outputs that match its own style. The median-of-three approach
produces more stable, fair evaluations.

### What does "low agreement" mean?

When the three Layer 2 models disagree significantly on an axis (standard
deviation > 1.5 on the 1-5 scale), that axis is flagged as "low agreement."
This typically means the task output is ambiguous or the models interpret the
evaluation criteria differently. The score is still valid but should be
interpreted with more caution.

### How do Elo ratings work?

After scoring, agents are compared pairwise. The agent with the higher overall
score "wins" the comparison. Elo ratings are updated with K-factor 32 and a
starting rating of 1000. Over many benchmark runs, Elo ratings converge to
reflect relative agent quality.

## Improving Your Score

### How can I improve my agent's score?

Focus on the lowest-scoring categories and checks first:

1. **Schema compliance:** Make sure your output matches the `output_schema`
   exactly. This is the most heavily weighted L1 check.
2. **Completeness:** Address every part of the task description.
3. **Required fields:** Never return empty or missing required fields.
4. **Time management:** Stay well within the time limit.
5. **Code quality:** For code tasks, ensure output parses without syntax errors.

### Why did my agent score 0 on a task?

Common causes:
- Agent endpoint was unreachable (check your endpoint URL and that the server
  is running).
- Agent returned a non-JSON response.
- Agent timed out after all retry attempts.
- Output was completely empty.

### Can I run only specific categories?

Yes. Configure categories in your `legit.yaml`:

```toml
[benchmark]
categories = ["code", "research"]
```

Or pass `--categories code,research` on the command line.

## Contributing

### How do I add a new benchmark task?

See the [Add New Benchmark](add-new-benchmark.md) guide.

### How do I contribute a task?

See the [Contributing Tasks](contribute-tasks.md) guide.

### Can I use a custom set of Layer 2 models?

Not currently. The three models (Claude, GPT-4o, Gemini) are
fixed to ensure consistent scoring across all users. Custom model support may
be added in a future release.
