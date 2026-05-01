# Coding Rules

## Before Editing

- Read the files you will modify and adjacent code paths.
- Preserve established patterns in `backend/app`, `openclaw`, `ops`, and `website`.
- Check applicable nested `AGENTS.md` files before editing under `openclaw/workspaces/**`.

## During Editing

- Make behavior-focused changes with minimal surface area.
- Keep deterministic state transitions in backend services, not in agent prompts.
- Use clear names and avoid unnecessary abstractions.
- Add comments only where logic is non-obvious.
- Do not introduce generated outputs, caches, credentials, local runtime state, or campaign data into Git.

## After Editing

- Sanity-check changed files for accidental regressions.
- Ensure external calls have explicit timeout/error handling.
- Keep docs current when behavior, setup, provider assumptions, or operating workflow changes.
