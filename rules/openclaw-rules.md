# OpenClaw Rules

## Runtime Boundary

- OpenClaw owns enrichment, contact discovery, site audit, draft generation, and reply classification.
- The Aperture backend owns send eligibility, persistence, dedupe, suppression, and campaign state.
- The agency OpenClaw runtime is separate from any personal desktop install.

## Workflow Changes

- When adding a new AI workflow, add or update:
  - an OpenClaw workflow prompt in `openclaw/workflows/`
  - backend job/service mapping when the workflow is callable from backend state
  - tests covering success and degraded-provider behavior when backend behavior changes

## Prompt Discipline

- Prompts must use only input evidence provided by the backend.
- Do not allow prompts to invent metrics, claims, contacts, or compliance status.
- Keep outputs strict and schema-like when backend code consumes them.
