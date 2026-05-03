# Agency Contact + Pitch Pack Contract

## 1) Task

- Title: Build agency contact discovery and pitch-pack stage
- Owner: Codex
- Date: 2026-05-03
- Scope: Add a second-stage prospecting script that turns approved agency accounts into clean contact candidates, best-contact decisions, and outreach-ready pitch packs.
- Out of scope: Automated sending, private/member-only scraping, paid contact enrichment APIs, and verified inbox deliverability checks.

## 2) Implementation Decisions

- Final approach: Keep account generation separate, use deterministic public search/page extraction for contact evidence, and make OpenClaw optional for top-N pitch refinement.
- Alternatives considered: A single all-purpose OpenClaw lead agent; rejected because it would be more expensive, harder to audit, and more likely to invent contact data.
- Dependencies impacted: `ops/prospecting`, OpenClaw workflow prompts, prospecting docs.

## 3) Acceptance Criteria

- [x] Script reads `agency_outreach_approval_<date>.csv` by default.
- [x] Script writes clean ignored output files under `data/prospects/`.
- [x] Contact rows include source URLs, confidence, and manual-verification status.
- [x] Pitch rows include LinkedIn/email drafts, Loom plan, assumptions, and do-not-claim guardrails.
- [x] OpenClaw is optional and capped by a top-N flag.

## 4) Verification Commands

### Scripts

- [x] `python -m py_compile ops\prospecting\enrich_agency_contacts.py`
- [x] Small smoke check: `python ops\prospecting\enrich_agency_contacts.py --dry-run --max-accounts 3 --max-contact-queries 2`
- [x] Sample run: `python ops\prospecting\enrich_agency_contacts.py --max-accounts 10 --max-contact-queries 4 --max-results-per-query 5 --request-delay 0.2 --source serper --openclaw-top-n 3 --openclaw-command C:\Users\athar\AppData\Roaming\npm\openclaw.cmd --openclaw-thinking low --openclaw-timeout 180`

## 5) Completion Record

- Summary of changes: Added `enrich_agency_contacts.py`, updated OpenClaw contact/draft prompts for structured outputs, documented the contact/pitch stage, and generated a 10-account review batch.
- Known risks: Search results can still include ambiguous people for common company names; every contact remains manual-review only before outreach.
- Follow-ups: Add a contact-verification provider later if reply quality justifies spend.
