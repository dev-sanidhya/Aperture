## 1) Task

- Title: Add research skipping and direct OpenClaw outreach refinement
- Owner: Codex
- Date: 2026-05-05
- Scope: Skip already-processed source domains during research and add a direct mode to refine existing outreach rows with OpenClaw.
- Out of scope: Automated sending, all-row OpenClaw run, paid API changes.

## 2) Implementation Decisions

- Final approach: Research skips domains from existing output files by default. OpenClaw refinement updates `outreach.csv` in place with `ai_enrichment_status`.
- Alternatives considered: Separate OpenClaw output file; rejected because `outreach.csv` should remain the one operator file.
- Dependencies impacted: prospecting research and contact enrichment scripts.

## 3) Acceptance Criteria

- [x] Research can skip domains already in `outreach.csv`/prior pipeline.
- [x] Existing outreach rows can be OpenClaw-refined without re-running contact discovery.
- [x] OpenClaw result still writes to `outreach.csv` with status.
- [x] Verification commands pass.

## 4) Verification Commands

### Scripts

- [x] python -m py_compile changed scripts
- [x] dry-run checks
- [x] small OpenClaw refinement attempt or explain why not run

## 5) Completion Record

- Summary of changes: Added processed-domain skipping in website research and direct OpenClaw refinement for existing `outreach.csv` rows.
- Known risks: The first OpenClaw attempt timed out at 120 seconds and marked the row `openclaw_timeout`; failed OpenClaw rows are skipped by default unless `--retry-openclaw-failures` is passed.
- Follow-ups: Tune OpenClaw timeout/model or prompt length before running large refinement batches.
