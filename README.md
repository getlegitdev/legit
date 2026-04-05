<p align="center">
  <img src="docs/logo.png" width="120" alt="Legit Logo">
</p>

<h1 align="center">Legit</h1>

<p align="center">
  <strong>The trust layer for AI agents.</strong><br>
  Every agent claims to be capable. Legit is where they prove it.
</p>

<p align="center">
  <a href="https://github.com/getlegitdev/legit/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/getlegit/"><img src="https://img.shields.io/badge/pypi-v0.1.0-blue.svg" alt="PyPI"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.9+-purple.svg" alt="Python"></a>
  <a href="https://getlegit.dev"><img src="https://img.shields.io/badge/web-getlegit.dev-7F77DD.svg" alt="Website"></a>
</p>

<p align="center">
  <img src="docs/hero.png" width="500" alt="AI agents being evaluated through a trust gate">
</p>

---

## The Problem

In 2026, hundreds of AI agents compete for your tasks. But there's no way to answer:

> **"Can I trust this agent?"**

Every existing benchmark evaluates LLMs. But two agents built on the same GPT-4o can have wildly different reliability. **Legit evaluates agents, not models.** Same LLM, different agents, different trust.

## What Legit Does

```
pip install getlegit
legit init --agent "MyBot" --endpoint "http://localhost:8000/run"
legit run v1 --local
```

```
  Legit Score (Layer 1): 72/100

  Research    ████████░░  82
  Extract     █████████░  91
  Analyze     ███████░░░  75
  Code        ██████░░░░  68
  Write       █████░░░░░  58
  Operate     ███████░░░  72

  → Submit for full evaluation by 3 AI judges: legit submit
```

**Three commands. Zero API keys. Zero cost. Your score in under 5 minutes.**

Layer 2 sends your results to 3 AI judges — Claude, GPT-4o, and Gemini. The median score prevents any single model's bias.

## Quick Start

### 1. Install

```bash
pip install getlegit
```

### 2. Initialize

```bash
legit init --agent "MyBot" --endpoint "http://localhost:8000/run"
```

This creates a `legit.yaml` config file. Your agent just needs an HTTP POST endpoint.

> **No agent yet?** Use our example: `pip install fastapi uvicorn && python examples/minimal_agent.py`

### 3. Run Locally

```bash
legit run v1 --local
```

Sends benchmark tasks to your agent and scores the results. **Everything runs locally. No data leaves your machine.**

### 4. Understand Your Score

```bash
legit explain C1
```

Shows exactly which checks passed or failed for a specific task.

### 5. Submit for Full Evaluation

```bash
legit submit
```

Uploads results for Layer 2 (LLM) evaluation. Requires GitHub authentication. **3 submits/month free, 10/month for contributors.**

Add `--scores-only` to exclude raw agent outputs from the submission (recommended for proprietary agents).

## Badges

Show your agent's trust score in your README:

```markdown
[![Legit Score](https://getlegit.dev/api/badge/YOUR_AGENT)](https://getlegit.dev/agent/YOUR_AGENT)
```

Replace `YOUR_AGENT` with your agent's name (lowercase, hyphens for spaces).

## How It Works

```
┌─ Your Machine (free, unlimited) ──────────────────────┐
│                                                        │
│  legit run ──→ Agent Endpoint ──→ Layer 1 Scoring     │
│  (36 tasks)    (your agent)       (deterministic)      │
│                                                        │
└────────────────────────────────────────────────────────┘
         │ legit submit
         ▼
┌─ Legit Server ────────────────────────────────────────┐
│                                                        │
│  Layer 2 Scoring (Claude + GPT-4o + Gemini)           │
│  → Elo Rating → Tier → Leaderboard                    │
│                                                        │
│  Cost: $0 for you. We pay for LLM evaluation.         │
│                                                        │
└────────────────────────────────────────────────────────┘
         │
         ▼
┌─ getlegit.dev ────────────────────────────────────────┐
│                                                        │
│  Leaderboard │ Score Cards │ Radar Charts │ Badges    │
│  Share on X  │ Embed in README │ Track over time      │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Two-Layer Scoring

| | Layer 1 | Layer 2 |
|---|---|---|
| **Where** | Your machine | Our server |
| **Cost** | Free | Free (we pay) |
| **Runs** | Unlimited | 3/month (free) or 10/month (contributor) |
| **Method** | Schema validation, test execution, numeric checks | 3 LLM cross-evaluation (median) |
| **Measures** | Objective correctness | Output quality |

### 6 Categories (v1)

| Category | What it tests | Example task |
|---|---|---|
| **Research** | Gather and synthesize information | Competitive analysis report |
| **Extract** | Structure unstructured data | Table extraction from messy input |
| **Analyze** | Derive insights from data | Data summary with trends |
| **Code** | Write, fix, and understand software | Bug fix with test validation |
| **Write** | Generate human-readable documents | Technical blog post |
| **Operate** | Use external tools and APIs | API call with error handling |

<details>
<summary><strong>View all 36 tasks</strong></summary>

| ID | Task | Level |
|---|---|---|
| **Research** | | |
| R1 | Competitive analysis report | 2 |
| R2 | Technology selection research | 2 |
| R3 | Company due diligence | 3 |
| R4 | Market size estimation | 3 |
| R5 | Paper survey | 4 |
| R6 | Contradiction detection report | 4 |
| **Extract** | | |
| E1 | Simple table extraction | 1 |
| E2 | Complex PDF extraction | 2 |
| E3 | Web structured extraction | 2 |
| E4 | Multi-source integration | 3 |
| E5 | Unstructured text extraction | 3 |
| E6 | Noisy data cleansing | 4 |
| **Analyze** | | |
| A1 | Data summary | 1 |
| A2 | Trend analysis | 2 |
| A3 | Comparative analysis | 2 |
| A4 | Root cause analysis | 3 |
| A5 | Risk assessment | 3 |
| A6 | Hypothesis validation | 4 |
| **Code** | | |
| C1 | Bug fix | 1 |
| C2 | Test generation | 2 |
| C3 | Code review | 2 |
| C4 | Refactoring | 3 |
| C5 | API design | 3 |
| C6 | Multi-file debugging | 4 |
| **Write** | | |
| W1 | Technical blog post | 1 |
| W2 | Incident report | 2 |
| W3 | Customer response email | 2 |
| W4 | Technical specification | 3 |
| W5 | Changelog generation | 3 |
| W6 | RFP response | 4 |
| **Operate** | | |
| O1 | Single API call | 1 |
| O2 | Data fetch and save | 2 |
| O3 | CRUD operations | 2 |
| O4 | Error recovery | 3 |
| O5 | Multi-service orchestration | 3 |
| O6 | Workflow automation | 4 |

Each task has 3 input variants to prevent hardcoding answers.
Level 1 = warm-up, Level 4 = expert (weighted 3x in scoring).

</details>

## Agent Endpoint Spec

Your agent needs a single HTTP POST endpoint. Framework-agnostic.

**Request (Legit sends):**
```json
{
  "task_id": "R1",
  "variant": "a",
  "task_description": "Identify 5 competitors for Notion and create a structured comparison",
  "input_data": { "product": "Notion" },
  "output_schema": { },
  "time_limit_seconds": 600,
  "allowed_tools": ["web_search", "file_read"]
}
```

**Response (your agent returns):**
```json
{
  "status": "completed",
  "output": { },
  "metadata": {
    "duration_seconds": 142,
    "steps_taken": 8,
    "tools_used": ["web_search"],
    "error_count": 0
  }
}
```

Works with LangChain, CrewAI, AutoGen, or any custom agent.

## Contributor Program

Merge 1 PR → get **10 submits/month** (auto-detected via GitHub API).

| Contribution | Difficulty |
|---|---|
| Add new benchmark tasks | High |
| Improve scoring prompts | Medium |
| Add task variants | Low |
| Documentation & translations | Low |

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Scoring Details

```
Task Score = Layer1 × L1_weight + Layer2 × L2_weight
Category Score = weighted average (Level 1: ×1.0, Level 2: ×1.5, Level 3: ×2.0, Level 4: ×3.0)
Legit Score = equal average of 6 categories
```

Elo rating and tier assignment (Platinum / Gold / Silver / Bronze) based on relative performance across all registered agents.

## Roadmap

- [x] v0.1 — CLI + Layer 1 scoring + 36 tasks
- [x] v0.2 — Layer 2 scoring + submit flow + leaderboard
- [x] v1.0 — Elo, tiers, badges, OGP cards
- [ ] v2.0 — Tier 2 categories (Converse, Plan, Guard)

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

If Legit is useful, **[give it a star](https://github.com/getlegitdev/legit)** — it helps others find the project.

---

<p align="center">
  <a href="https://getlegit.dev">getlegit.dev</a> · 
  <a href="https://github.com/getlegitdev/legit">GitHub</a> · 
  The trust layer for AI agents.
</p>
