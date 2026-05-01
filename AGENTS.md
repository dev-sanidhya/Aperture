# Aperture Agent Router

This file is a routing index. Keep it short and treat referenced files as source of truth.

## Always Do First

1. Read [rules/general-workflow-rules.md](rules/general-workflow-rules.md).
2. If writing or editing code, read [rules/coding-rules.md](rules/coding-rules.md).
3. For non-trivial work, create a task contract from [contracts/TASK_CONTRACT_TEMPLATE.md](contracts/TASK_CONTRACT_TEMPLATE.md).
4. For small/low-risk work, keep a mini-contract in task notes: scope, acceptance checks, and commands to run.

## Conditional Routing

- If touching backend code (`backend/app/**`): read [rules/backend-rules.md](rules/backend-rules.md).
- If touching database models or migrations (`backend/app/models/**`, `backend/alembic/**`): read [rules/data-rules.md](rules/data-rules.md).
- If touching discovery, outreach, provider integrations, or external APIs: read [rules/integration-rules.md](rules/integration-rules.md).
- If touching OpenClaw prompts/workspaces (`openclaw/**`): read [rules/openclaw-rules.md](rules/openclaw-rules.md).
- If touching static site or public copy (`website/**`): read [rules/website-rules.md](rules/website-rules.md).
- If touching ops/deployment/runtime (`ops/**`, `docs/deployment.md`, provider setup docs): read [rules/ops-rules.md](rules/ops-rules.md).
- If touching secrets, suppression, send eligibility, WhatsApp, email dispatch, webhooks, or contact data: read [rules/security-rules.md](rules/security-rules.md).
- If writing tests or changing test files: read [rules/testing-rules.md](rules/testing-rules.md).
- If tests fail: read [rules/failing-tests-rules.md](rules/failing-tests-rules.md).

## Completion Gates

Do not mark a task complete until the relevant verification commands pass, or explicitly report why they were not run.

- Backend/code changes:
  - `python -m pytest backend\tests`
- Single module or focused bug fix:
  - Run the smallest relevant `python -m pytest ...` target first, then the full backend gate when practical.
- Prospecting/ops script changes:
  - `python -m py_compile <changed-script>`
  - Run a no-network or small-output smoke check when possible.
- Website changes:
  - Inspect affected HTML/CSS manually.
  - If visual behavior changed, capture screenshot evidence and reference the file path in the summary.
- Cross-stack changes: run all relevant gates.

## Skill Routing

- Use skills for repeatable workflows, not personal preferences. Keep durable preferences in `rules/*.md`.

## Maintenance

- Before adding a new rule/skill, first check whether an existing rule can be updated.
- For recurring mistakes, add one concise rule to [rules/maintenance-rules.md](rules/maintenance-rules.md).
- Keep completed contracts in `contracts/` as task history, but do not load old contracts unless directly relevant.
- For every non-trivial completed task, append a short retro using [contracts/TASK_RETRO_TEMPLATE.md](contracts/TASK_RETRO_TEMPLATE.md).

## Git

- Commit in small increments.
- Push to `origin` when a genuine unit of work is complete: a working feature slice, a cleanup with validated diff, a documentation update that changes operating behavior, or a tested bug fix.
- Keep activity real. Do not create noise commits, whitespace-only commits, meaningless file churn, or pushes that cannot be explained as useful project progress.
- Prefer multiple small, coherent pushes over holding a large mixed batch locally. If work spans more than one concern, split it into separate commits before pushing.
- Do not mix unrelated cleanup into feature commits.
