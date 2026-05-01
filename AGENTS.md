# Aperture Agent Guide

This repository is the codebase for `Aperture`, an India-focused outbound agency engine. Keep changes aligned to the product shape below.

## Core architecture

- Deterministic backend code owns persistence, dedupe, routing, suppression, send caps, campaign state, provider webhooks, and analytics.
- OpenClaw owns agentic tasks: enrichment, contact discovery, site audit, draft generation, and reply classification.
- The agency OpenClaw runtime is separate from any personal desktop install. Treat it as a dedicated host-side dependency that runs on the Aperture deployment target.

## Repository layout

- `backend/app/api`: HTTP routes and webhook endpoints
- `backend/app/models`: SQLAlchemy domain models
- `backend/app/services`: deterministic business logic
- `backend/app/integrations`: provider integrations
- `backend/app/workers`: Dramatiq jobs
- `openclaw/`: Aperture-specific OpenClaw config and workflow prompts
- `ops/`: deployment, runtime, and environment setup
- `docs/`: architecture and setup docs

## Working rules

- Preserve the split between deterministic state transitions and agent output.
- Do not let OpenClaw send messages directly. All sends must flow through backend eligibility checks.
- Keep WhatsApp cold outreach behind explicit eligibility checks and suppression rules.
- Use public business contacts only.
- Prefer explicit schemas and durable storage over ad hoc JSON blobs unless the data is truly provider-native.
- When adding a new AI workflow, add:
  - an OpenClaw workflow prompt in `openclaw/workflows/`
  - a job type or service mapping in the backend
  - tests that cover success and degraded-provider behavior

## Validation

- Run `python -m pytest backend\tests` before pushing.
- If you add or change models, add/update Alembic migrations.
- Keep docs current when changing deployment or provider setup.

## Git

- Commit in small increments.
- Push frequently to `origin` when a genuine unit of work is complete: a working feature slice, a cleanup with validated diff, a documentation update that changes operating behavior, or a tested bug fix.
- Keep activity real. Do not create noise commits, whitespace-only commits, meaningless file churn, or pushes that cannot be explained as useful project progress.
- Prefer multiple small, coherent pushes over holding a large mixed batch locally. If work spans more than one concern, split it into separate commits before pushing.
- Do not mix unrelated cleanup into feature commits.

