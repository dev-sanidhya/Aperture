# Failing Tests Rules

## Failure Handling

- Stop adding features when tests fail unexpectedly.
- Triage failures by root cause and fix one class of failure at a time.

## Debug Flow

1. Reproduce locally with the exact command.
2. Isolate whether the failure is deterministic or flaky.
3. Check recently touched files first.
4. Apply the minimal fix.
5. Re-run the failing set, then broader required gates.

## Guardrails

- Do not bypass failing tests with skips, assertion dilution, or broad mocking without explicit approval.
