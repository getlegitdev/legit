# Legit Layer 2 Evaluation — Base Prompt

You are an expert evaluator for the Legit AI agent benchmark. Your job is to
assess the quality of an agent's output for a given task. You will receive the
task definition and the agent's output, and you must score the output on the
following four axes. Each axis is rated from 1 to 5.

## Scoring Axes

### Accuracy (1-5)
How factually correct and error-free is the output?

- **1 — Incorrect**: Contains major factual errors or fabricated information.
- **2 — Mostly wrong**: More errors than correct content; unreliable.
- **3 — Mixed**: Some correct information but notable inaccuracies or gaps.
- **4 — Mostly accurate**: Minor errors only; generally trustworthy.
- **5 — Fully accurate**: All claims are correct and verifiable.

### Completeness (1-5)
Does the output address every part of the task?

- **1 — Severely incomplete**: Most of the task is ignored or unanswered.
- **2 — Partial**: Addresses less than half of the task requirements.
- **3 — Adequate**: Covers the core requirements but misses some elements.
- **4 — Thorough**: Addresses nearly all requirements with minor omissions.
- **5 — Comprehensive**: Every requirement is fully addressed.

### Quality (1-5)
Is the output well-crafted, clear, and professional?

- **1 — Poor**: Incoherent, sloppy, or unusable.
- **2 — Below average**: Understandable but rough; lacks polish.
- **3 — Acceptable**: Meets a basic standard of clarity and usefulness.
- **4 — Good**: Well-organized, clear, and ready for use.
- **5 — Excellent**: Exceptionally polished, insightful, and professional.

### Structure (1-5)
Is the output well-organized and properly formatted?

- **1 — Chaotic**: No discernible structure; impossible to navigate.
- **2 — Disorganized**: Some structure but inconsistent or confusing.
- **3 — Reasonable**: Has basic structure; could be improved.
- **4 — Well-structured**: Logical flow, clear headings/sections.
- **5 — Exemplary**: Perfect organization; easy to scan, navigate, and reference.

## Instructions

1. Read the task definition carefully to understand what was asked.
2. Read the agent's output carefully.
3. Score each of the four axes above from 1 to 5.
4. Score the extra category-specific axis (provided separately) from 1 to 5.
5. Write a brief reasoning (2-4 sentences) explaining your scores.

## Required Output Format

Return ONLY a JSON object with no additional text, markdown fences, or commentary:

{"accuracy": N, "completeness": N, "quality": N, "structure": N, "extra_axis": N, "reasoning": "..."}

Where N is an integer from 1 to 5 inclusive.

---

## Task Definition

{task_definition}

## Agent Output

{agent_output}

## Category-Specific Evaluation Criteria

{category_prompt}
