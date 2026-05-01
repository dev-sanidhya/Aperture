# Backend Rules

## Core Expectations

- Keep API behavior backward compatible unless the task explicitly changes contracts.
- Preserve the split between deterministic backend code and agentic OpenClaw output.
- Backend code owns persistence, dedupe, routing, suppression, send caps, campaign state, provider webhooks, and analytics.
- Prefer explicit schemas and durable storage over ad hoc JSON blobs unless the data is provider-native or intentionally unstructured.

## Required Verification

- Run `python -m pytest backend\tests` for backend behavior changes.
- For focused changes, run the smallest relevant test file first.

## Data and Campaign Safety

- Do not let OpenClaw send messages directly. All sends must flow through backend eligibility checks.
- Keep cold outreach routing behind suppression, eligibility, and send-cap logic.
- Do not weaken idempotency, dedupe, or suppression behavior to make a flow easier to run.
