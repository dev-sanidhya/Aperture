# Serper + Copilot Routing Contract

## 1) Task

- Title: Configure Serper discovery and Copilot-first OpenClaw routing
- Owner: Codex
- Date: 2026-05-03
- Scope: Keep Serper credentials local-only, make Copilot the default OpenClaw provider, use Codex as cheaper fallback, and report the generated agency leads/enrichment sample.
- Out of scope: Automated sending, paid contact data providers, LinkedIn scraping, and committing generated prospect data.

## 2) Implementation Decisions

- Final approach: Update OpenClaw examples/local config to primary `github-copilot/gpt-5.3-codex` with fallback `openai-codex/gpt-5.2-codex`; adjust backend routing and prospecting defaults to use Copilot first.
- Alternatives considered: Copilot `gpt-5.4`, but the local provider previously rejected it despite listing it; direct Codex `gpt-5.4`, but it is more expensive/quota-sensitive for this phase.
- Dependencies impacted: OpenClaw local config, OpenClaw example config, backend job routing, prospecting docs and script defaults.

## 3) Acceptance Criteria

- [x] Serper key is not added to tracked files.
- [x] Default OpenClaw enrichment path is Copilot-first.
- [x] Codex fallback uses a cheaper Codex model than `openai-codex/gpt-5.4`.
- [x] Generated lead data remains under ignored `data/`.
- [x] The exact approval leads and one enrichment example are reported.

## 4) Verification Commands

### Backend

- [x] `python -m pytest backend\tests`

### Scripts

- [x] `python -m py_compile ops\prospecting\build_agency_pipeline.py`
- [x] `python -m py_compile ops\prospecting\discover_agencies.py`
- [x] `python ops\prospecting\discover_agencies.py --dry-run --source serper --max-queries 2`
- [x] Small prospecting smoke check: `python ops\prospecting\discover_agencies.py --source serper --segment b2b-lead-gen --segment paid-media-seo --segment revops-hubspot --country "United States" --country "United Kingdom" --max-queries 12 --max-results-per-query 10 --max-results 120 --min-score 45`
- [x] Deterministic pipeline run: `python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_2026-05-03.csv" --max-sites 30 --request-delay 0.2`

## 5) Completion Record

- Summary of changes: Serper is configured locally, discovery loads root `.env`, OpenClaw defaults and backend routing are Copilot-first, and Codex fallback uses `openai-codex/gpt-5.2-codex`.
- Known risks: Copilot `gpt-5.4` was not selected because the provider previously rejected it even though it appeared in the catalog; Serper result quality still needs manual review before outreach.
- Follow-ups: Add decision-maker/contact discovery before sending and keep OpenClaw top-N low until reply quality is proven.
