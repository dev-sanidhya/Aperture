## 1) Task

- Title: Simplify prospecting output structure
- Owner: Codex
- Date: 2026-05-05
- Scope: Change prospecting scripts to write to one stable active batch folder with predictable filenames, update docs, and move the current usable outputs into that structure.
- Out of scope: Sending outreach, changing scoring/enrichment behavior, deleting historical generated data unless it is archived under data/.

## 2) Implementation Decisions

- Final approach: Use `data/prospects/current/` as the default active batch directory. Scripts keep optional output overrides for custom runs.
- Alternatives considered: More timestamped run folders; rejected because the user needs fewer files and less ambiguity right now.
- Dependencies impacted: ops prospecting scripts and docs.

## 3) Acceptance Criteria

- [x] Directory import defaults to stable current filenames.
- [x] Discovery defaults to stable current filenames.
- [x] Website research defaults to stable current filenames.
- [x] Contact/pitch enrichment defaults to stable current filenames.
- [x] Docs identify exactly which files to use.
- [x] Current usable outreach files are available under the new structure.

## 4) Verification Commands

### Scripts

- [x] python -m py_compile changed scripts
- [x] No-network or small-output smoke check

## 5) Completion Record

- Summary of changes: Prospecting scripts now default to `data/prospects/current/` with stable stage filenames, docs point to the new structure, and existing root-level generated files were archived under `data/prospects/archive/legacy-root-2026-05-05/`.
- Known risks: Rerunning a stage overwrites the active `current/` files by design; copy `current/` to an archive folder first if a batch must be preserved.
- Follow-ups: Add a single orchestrator command if the three-step manual run still feels clunky.
