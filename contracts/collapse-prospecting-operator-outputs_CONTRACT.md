## 1) Task

- Title: Collapse prospecting outputs to operator files
- Owner: Codex
- Date: 2026-05-05
- Scope: Present only root-level operator files and move stage/debug outputs under data/prospects/internal.
- Out of scope: Changing enrichment logic, sending outreach, deleting archived historical files.

## 2) Implementation Decisions

- Final approach: Root output files are `sources.csv`, `outreach.csv`, and `review.md`; stage files live in `data/prospects/internal/`.
- Alternatives considered: Numbered current files; rejected because it still exposes pipeline internals to the operator.
- Dependencies impacted: prospecting scripts and docs.

## 3) Acceptance Criteria

- [x] User-facing outputs are at most three root-level files.
- [x] Internal stage outputs are still available for debugging/reruns.
- [x] Script defaults use the new layout.
- [x] Docs explain which files matter.

## 4) Verification Commands

### Scripts

- [x] python -m py_compile changed scripts
- [x] dry-run checks

## 5) Completion Record

- Summary of changes: Collapsed operator-facing files to `data/prospects/sources.csv`, `data/prospects/outreach.csv`, and `data/prospects/review.md`; moved stage/debug files under `data/prospects/internal/`; updated scripts and docs.
- Known risks: A stale hidden `data/prospects/current/` folder may remain locally if another process holds a file handle, but scripts no longer use it.
- Follow-ups: Add an orchestrator command if the user wants one command to refresh all three operator files.
