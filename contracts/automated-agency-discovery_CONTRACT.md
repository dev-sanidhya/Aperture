# Automated Agency Discovery Contract

## 1) Task

- Title: Add API and web-search based B2B agency discovery
- Owner: Codex
- Date: 2026-05-03
- Scope:
  - Add a discovery script that can create candidate B2B agency account lists from API/search/list-page sources.
  - Keep discovery deterministic, stateful, and low-cost by default.
  - Produce CSV outputs that feed the existing agency enrichment pipeline.
  - Add provider configuration docs without committing secrets.
- Out of scope:
  - Production outreach sending.
  - LinkedIn scraping or private/member-only scraping.
  - Paid provider account setup.
  - Agent-owned web crawling.

## 2) Implementation Decisions

- Final approach:
  - Use Python for query generation, provider calls, domain extraction, dedupe, scoring, and queue outputs.
  - Support Brave Search, SerpAPI, Google Programmable Search, DuckDuckGo HTML as opportunistic fallback, seed URL files, and public list-page extraction.
  - Feed qualified account CSVs into `build_agency_pipeline.py --input-csv`.
  - Reserve OpenClaw for later deep enrichment after discovery has narrowed candidates.
- Alternatives considered:
  - Letting OpenClaw browse for leads end-to-end: rejected for v1 because it is expensive, harder to dedupe, and has weaker state guarantees.
  - Apollo API first: deferred because API access and enrichment consume credits and may require a paid plan.
  - Clay-style hosted orchestration: deferred to keep startup costs minimal.
- Dependencies impacted:
  - `ops/prospecting/**`
  - `ops/.env.example`
  - `docs/**`

## 3) Acceptance Criteria

- [x] Discovery can run without paid APIs using seed/list sources.
- [x] Discovery supports API-backed web search providers through env vars or CLI keys.
- [x] Discovery writes raw results, deduped accounts, research queue, and URL seed outputs under ignored `data/prospects/`.
- [x] Existing enrichment script can consume the generated research queue CSV.
- [x] Docs explain the discovery-to-enrichment workflow and provider tradeoffs.

## 4) Verification Commands

### Backend

- [x] Not run; ops scripts/docs only.

### Focused Tests

- [x] Not run; no backend behavior changed.

### Scripts

- [x] `python -m py_compile ops\prospecting\discover_agencies.py`
- [x] `python -m py_compile ops\prospecting\build_agency_pipeline.py`
- [x] Small smoke check: `python ops\prospecting\discover_agencies.py --dry-run`
- [x] Small smoke check: `python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 10 --min-score 45`
- [x] API config smoke check: `python ops\prospecting\discover_agencies.py --source brave --dry-run --segment b2b-lead-gen --country "United States" --max-queries 4`
- [x] Intake smoke check: `python ops\prospecting\build_agency_pipeline.py --no-search --input-csv data\prospects\agency_research_queue_2026-05-03.csv --max-sites 3 --max-pages-per-site 1 --request-delay 0.2 --min-score 0`

### Website

- [ ] Not applicable.

## 5) Completion Record

- Summary of changes:
  - Added `discover_agencies.py` for API/search/list/seed based agency account discovery.
  - Added discovery source examples and provider env vars.
  - Updated the existing enrichment script to preserve discovery source metadata from imported queues.
  - Updated docs so the operating flow is discovery first, enrichment second, OpenClaw only after narrowing.
- Known risks:
  - Search providers require keys for reliable automation; DuckDuckGo HTML remains opportunistic and may throttle.
  - Public list pages may block requests or contain weak outbound links.
  - Discovery scoring is intentionally lightweight and still requires enrichment/manual verification.
- Follow-ups:
  - Add Hunter/Tomba/Apollo contact discovery after the account discovery layer proves useful.
  - Add provider-specific unit tests with fixture JSON if this becomes a shared production integration.
