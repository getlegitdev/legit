# Operate Category — Extra Axis: Reliability

### reliability (1-5)
Does the agent output demonstrate proper error handling, defensive practices, and robustness?

- **1 — Fragile**: No error handling; will fail on any unexpected input.
- **2 — Brittle**: Minimal error handling; likely to break in common edge cases.
- **3 — Adequate**: Handles the happy path and some errors, but gaps remain.
- **4 — Robust**: Comprehensive error handling; gracefully degrades on most failures.
- **5 — Production-grade**: Handles all foreseeable failures, includes logging/retry logic, and follows operational best practices.

When scoring reliability, consider:
- Are errors caught and handled rather than silently ignored or left to crash?
- Are retries, timeouts, and fallback strategies present where appropriate?
- Is input validation performed?
- Would this output be safe to deploy in a production environment?
