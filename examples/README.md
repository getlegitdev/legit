# Legit Examples

## Minimal Agent

A simple FastAPI server that responds to Legit benchmark requests with template data. No LLM needed -- just copy, paste, and run to see how Legit works.

### Setup

```bash
# Install dependencies
pip install fastapi uvicorn

# Start the agent
python examples/minimal_agent.py
```

The agent starts on `http://localhost:8000` with a single `POST /run` endpoint.

### Run the benchmark

In a second terminal:

```bash
pip install getlegit
legit init --agent "MinimalBot" --endpoint "http://localhost:8000/run"
legit run v1 --local
```

You should see scores for all 6 categories within a couple of minutes.

### How it works

The agent dispatches on the first character of the `task_id`:

| Prefix | Category | Response |
|--------|----------|----------|
| R | Research | 5-item competitor comparison |
| E | Extract | Headers + rows table |
| A | Analyze | Statistics, trends, insights |
| C | Code | Fixed code + bug description |
| W | Write | Title + body + tags |
| O | Operate | Status code + response data |

Scores will be low (the responses are static templates), but it demonstrates the full Legit evaluation loop end-to-end.

### Next steps

- Replace template responses with actual LLM calls
- Add tool integrations (web search, code execution)
- Run `legit submit` to get Layer 2 (LLM judge) evaluation
