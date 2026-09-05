# Workspace execution rules

- Work autonomously through implementation, debugging, validation, and iteration.
- When a command or test fails, inspect the failure, fix the relevant code or configuration, and rerun the focused check.
- Do not pause to ask for confirmation for ordinary file changes, dependency installation, test runs, refactors, or local server startup.
- Continue until the requested project behavior is complete and validated.
- Keep changes scoped to the request and preserve unrelated user work.
- Do not use destructive commands such as hard resets, force deletion, or overwriting unrelated files without explicit authorization.
- Do not fabricate successful runtime or test results. If an external prerequisite blocks execution, record the exact blocker and continue with static validation or other work that remains possible.
- Prefer local/mock fallbacks when cloud credentials or network services are unavailable.
