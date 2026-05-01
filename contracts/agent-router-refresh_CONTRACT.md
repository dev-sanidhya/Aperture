# Agent Router Refresh Contract

## 1) Task

- Title: Agent router refresh
- Owner: Codex
- Date: 2026-05-01
- Scope: Adapt the Bliss-style `AGENTS.md` router pattern into Aperture with project-specific rules, contracts, completion gates, and Git activity guidance.
- Out of scope: Changing backend/runtime behavior, changing OpenClaw workflow prompts, or creating new automation skills.

## 2) Implementation Decisions

- Final approach: Keep root `AGENTS.md` short as a router, move durable instructions into focused `rules/*.md`, and add reusable task contract/retro templates.
- Alternatives considered: Expanding the single root `AGENTS.md`; rejected because it creates context bloat and makes conditional rules harder to follow.
- Dependencies impacted: Agent workflow documentation only.

## 3) Acceptance Criteria

- [x] Root `AGENTS.md` routes agents to focused source-of-truth rule files.
- [x] Aperture-specific backend, OpenClaw, ops, integration, security, data, website, testing, and maintenance rules exist.
- [x] Task contract and retro templates exist.
- [x] Git guidance keeps frequent pushes genuine and reviewable.

## 4) Verification Commands

### Documentation

- [x] Manual diff review of `AGENTS.md`, `rules/*.md`, and `contracts/*.md`.
- [x] Link/path sanity check for all referenced rule and contract files.

## 5) Completion Record

- Summary of changes: Reworked agent instructions into a Bliss-inspired router and added Aperture-specific rule/contract files.
- Known risks: Rules may need pruning after real usage if any section proves too heavy.
- Follow-ups: Promote recurring mistakes into `rules/maintenance-rules.md` only when they generalize.

## Retro

- What worked: The Bliss pattern translated cleanly once project-specific routing paths were identified.
- What failed: Nothing material.
- Root cause, if failed: N/A.
- Repeatable rule candidate? no.
- If yes, proposed 1-line rule: N/A.
- Promote to skill candidate? no.
