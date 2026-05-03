# General Workflow Rules

## Product Context

- Aperture is an outbound agency engine for discovering, qualifying, enriching, routing, and contacting business prospects.
- The current commercial direction is AI-assisted workflow implementation for recruiting/staffing agencies; preserve support for broader outbound infrastructure unless the task explicitly narrows it.
- For business strategy, outreach, ICP, offer, and current batch context, use `docs/agency-strategy-context.md` as the source of truth.
- Keep the system grounded in public business evidence, compliant contact handling, and measurable outreach operations.

## Research vs Implementation

- Separate discovery from coding whenever architecture, data flow, or target segment is unclear.
- If a task changes positioning, ICP, or acquisition workflow, document the decision before changing implementation.
- Start implementation only after the source of truth, impacted paths, and acceptance checks are explicit.

## Scope Control

- Solve only the requested task scope.
- Avoid unrelated refactors unless required to unblock the task.
- Prefer small, reviewable diffs with clear ownership.
- Allow larger coordinated diffs only when the task explicitly requires cross-cutting behavior or atomic multi-file changes.

## Plan Discipline

- For non-trivial tasks, keep a short plan and update it as work progresses.
- Re-read the plan before each major change batch.
- For recurring process failures, capture one concise improvement in `rules/maintenance-rules.md`.

## Verification Discipline

- Prefer deterministic checks over intuition.
- Run the smallest relevant check early, then broader gates before completion when practical.
- Report exactly what was run, what was not run, and why.
