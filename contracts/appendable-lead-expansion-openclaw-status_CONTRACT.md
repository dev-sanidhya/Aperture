## 1) Task

- Title: Appendable lead expansion and OpenClaw status tracking
- Owner: Codex
- Date: 2026-05-05
- Scope: Make source/outreach outputs append+dedupe by default, track OpenClaw enrichment status in outreach rows, and run another expansion batch.
- Out of scope: Automated sending, full all-1900 enrichment, paid provider changes.

## 2) Implementation Decisions

- Final approach: Keep `sources.csv` and `outreach.csv` as operator-facing stores, append by domain/profile URL, and put OpenClaw output back into `outreach.csv` with explicit status.
- Alternatives considered: Separate OpenClaw output file; rejected because user wants a single outreach file.
- Dependencies impacted: prospecting importer, contact enrichment script, docs.

## 3) Acceptance Criteria

- [x] Source collector appends/dedupes into `sources.csv` by default.
- [x] Contact enrichment appends/dedupes into `outreach.csv` by default.
- [x] OpenClaw-enriched rows are visibly marked in `outreach.csv`.
- [x] Docs explain where OpenClaw output goes.
- [x] Another source/research/enrichment batch is run or clearly blocked.

## 4) Verification Commands

### Scripts

- [x] python -m py_compile changed scripts
- [x] dry-run checks
- [x] small or real pipeline batch

## 5) Completion Record

- Summary of changes: Added append/dedupe behavior for `sources.csv` and `outreach.csv`, added `ai_enrichment_status`, documented OpenClaw output behavior, expanded sources to 2,912 rows, and appended a 33-account enrichment batch to reach 107 outreach rows.
- Known risks: Website research still processes from the top of `sources.csv`; a cursor/processed marker would make future expansion more efficient.
- Follow-ups: Add a batch cursor or `processed_domains.csv` so future runs skip already-researched sources automatically.
