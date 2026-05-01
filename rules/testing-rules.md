# Testing Rules

## Test Change Policy

- Do not edit tests to make failures disappear unless explicitly requested.
- Prefer fixing production code over weakening assertions.

## Coverage Expectations

- Add or update tests when behavior changes.
- Cover success and degraded-provider behavior for backend-owned AI workflow integrations.
- Keep integration tests aligned with API/runtime behavior.

## Execution

- Run the smallest relevant test set early.
- Run `python -m pytest backend\tests` before completion for backend behavior changes when practical.
- For scripts, at minimum run `python -m py_compile <changed-script>` and a small smoke check when possible.
