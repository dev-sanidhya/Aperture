# B2B Agency Lead Pipeline Contract

## 1) Task

- Title: Replace recruiting prospecting with low-cost B2B agency lead pipeline
- Owner: Codex
- Date: 2026-05-03
- Scope:
  - Replace the old recruiting/staffing-only prospecting script and runbook with a B2B agency lead pipeline.
  - Keep discovery deterministic and low-cost using public search, seed URLs, and optional CSV imports.
  - Add optional OpenClaw enrichment for only top-fit leads, with human review before outreach.
  - Update strategy/runtime docs so the operating model is ready for first outreach tomorrow.
- Out of scope:
  - Production email sending.
  - Paid API integrations such as Apollo, Clay, SerpAPI, Instantly, or Smartlead.
  - Fully autonomous outbound or LinkedIn automation.

## 2) Implementation Decisions

- Final approach:
  - Use Python pipeline code for discovery, dedupe, website extraction, deterministic fit scoring, and approval-batch generation.
  - Use OpenClaw as optional enrichment only after deterministic scoring, capped by `--openclaw-top-n`.
  - Write generated prospect files under ignored `data/prospects/`.
- Alternatives considered:
  - Hermes/OpenClaw as an always-on SDR: rejected for v1 because it is harder to debug, harder to control spend, and not needed for first signal.
  - Claude Agent SDK: rejected for now because the user does not want another paid Claude/API setup.
  - Paid discovery APIs first: deferred until the first reply/close signal justifies spend.
- Dependencies impacted:
  - `ops/prospecting/**`
  - `docs/agency-strategy-context.md`
  - `README.md`
  - `docs/openclaw-hosting.md`

## 3) Acceptance Criteria

- [x] Prospecting command creates B2B-agency CSV/runbook outputs without requiring paid APIs.
- [x] Optional OpenClaw enrichment is explicit, capped, and disabled by default.
- [x] Old recruiting/staffing-only setup is no longer the documented primary pipeline.
- [x] Docs explain the low-cost startup setup and why OpenClaw is used only after deterministic scoring.

## 4) Verification Commands

### Backend

- [x] `python -m pytest backend\tests\unit\test_openclaw_runtime.py`

### Focused Tests

- [x] `python ops\prospecting\build_agency_pipeline.py --no-search --seed-file ops\prospecting\agency_seed_urls.example.txt --max-sites 3 --max-pages-per-site 1 --request-delay 0.2 --min-score 0`
- [x] `python ops\prospecting\build_agency_pipeline.py --no-search --seed-file ops\prospecting\agency_seed_urls.example.txt --max-sites 25 --max-pages-per-site 2 --request-delay 0.4 --min-score 70`

### Scripts

- [x] `python -m py_compile ops\prospecting\build_agency_pipeline.py`
- [x] Small smoke check: `python ops\prospecting\build_agency_pipeline.py --dry-run`

### Website

- [ ] Not applicable.

## 5) Completion Record

- Summary of changes:
  - Removed the old recruiting-only prospecting script/runbook/seeds.
  - Added the B2B agency pipeline script, seed examples, operating runbook, and task contract.
  - Updated docs and OpenClaw prompts to use deterministic discovery plus optional capped enrichment.
  - Lowered the example Codex budget cap and moved model references to the mini route.
- Known risks:
  - DuckDuckGo HTML search can throttle or change markup; import CSV/seed URLs remain fallback paths.
  - Public website extraction is intentionally lightweight and still needs manual decision-maker verification.
  - OpenClaw enrichment was not invoked in verification to avoid model spend.
- Follow-ups:
  - Add an approved-prospect CRM table or Airtable export after the first reply signal.
  - Add a sequencing-provider integration only after sender domain and opt-out handling are ready.

## Retro

- What worked:
  - Keeping discovery deterministic made the first working version cheap and testable.
- What failed:
  - No failure.
- Root cause, if failed:
  - Not applicable.
- Repeatable rule candidate? (yes/no):
  - yes
- If yes, proposed 1-line rule:
  - Use deterministic sourcing and scoring first; reserve agents for capped enrichment after fit has already been established.
- Promote to skill candidate? (yes/no):
  - no
