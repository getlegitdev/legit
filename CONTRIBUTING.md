# Contributing to Legit

Thank you for your interest in contributing to Legit! Every contribution helps build better trust infrastructure for AI agents.

**New here?** Check out issues labeled [`good first issue`](https://github.com/getlegitdev/legit/labels/good%20first%20issue) to get started.

## Development Setup

### Python CLI
```bash
git clone https://github.com/getlegitdev/legit.git
cd legit
python -m venv .venv
source .venv/bin/activate
pip install -e .
legit --version
```

### Web (getlegit.dev)
```bash
cd web
npm install
npm run dev
# Open http://localhost:4321
```

## Quick Start

1. Fork the repository
2. Create a feature branch: `git checkout -b my-feature`
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## Contribution Types

### Add Benchmark Tasks (High Impact)
Create new task definitions in `src/getlegit/benchmarks/v1/tasks/`. Each task needs:
- `task.json` - Task definition
- `variants/a.json`, `b.json`, `c.json` - Input variants
- `ground_truth/a.json`, `b.json`, `c.json` - Expected outputs

### Improve Scoring (Medium Impact)
- Fix Layer 1 checkers in `src/getlegit/judges/layer1/`
- Improve Layer 2 prompts in `src/getlegit/judges/layer2/prompts/`

### Add Variants (Low Effort)
Add new input variations for existing tasks. Great first contribution!

### Documentation
README improvements, FAQ, translations.

## Review Process

We aim to review PRs within 48 hours. For larger changes, open an issue first to discuss the approach.

## Contributor Benefits

Contributors with 1+ merged PR automatically get **10 submits/month** (vs 3 for free users). No application needed - it's detected automatically via the GitHub API.

## Code Style

- Python: Ruff for linting, type hints encouraged
- Web: Prettier for formatting
- Commit messages: imperative mood ("Add feature" not "Added feature")

## Code of Conduct

Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.
