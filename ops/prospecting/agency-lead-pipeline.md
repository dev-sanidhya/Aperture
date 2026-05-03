# B2B Agency Lead Pipeline

## Goal

Build a daily list of B2B agencies that are likely to pay for practical AI workflow implementation around revenue ops, client reporting, follow-up, proposal, CRM, and delivery handoff workflows.

This pipeline is designed for low-cost early validation. It does not require paid lead APIs, and it does not send outreach automatically.

## ICP

- Geography: United States, United Kingdom, Canada, Australia
- Company type: B2B marketing, lead-generation, paid media, SEO, HubSpot/RevOps, recruiting/staffing, product/dev, or growth agencies
- Size: roughly 10-50 employees, with room to test 5-100
- Buyer: founder, CEO, managing director, COO, head of client services, head of operations, head of RevOps, head of recruitment

## Best Initial Segments

1. B2B lead-generation and growth agencies
2. Paid media / SEO agencies serving B2B or SaaS clients
3. HubSpot / RevOps agencies
4. Recruiting/staffing agencies as a sub-segment, not the whole market

## Offer Angles

Use the script's `pain_angle` field to decide the first message.

- `call_to_proposal`: call transcript to CRM notes, follow-up, proposal outline, and internal tasks
- `client_reporting_insights`: campaign/reporting data to client-ready insights and account-manager drafts
- `lead_intake_crm_followup`: lead intake to enrichment, qualification, CRM update, and follow-up drafts
- `delivery_handoff_ops`: client intake to project brief, tasks, owners, and handoff updates
- `recruiting_ops`: candidate/client notes to shortlists, outreach, follow-ups, and ATS updates

## Local Build

Run from the repo root:

```powershell
python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 50 --min-score 45
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30
```

Generated files are written under ignored `data/prospects/`:

- `agency_discovery_raw_<date>.csv`: raw API/search/list/seed results
- `agency_accounts_discovered_<date>.csv`: deduped discovered accounts
- `agency_research_queue_<date>.csv`: qualified accounts to enrich
- `agency_discovered_seed_urls_<date>.txt`: URL-only queue for seed-based runs
- `agency_discovery_runbook_<date>.md`: discovery run notes
- `agency_pipeline_<date>.csv`: all researched agencies
- `agency_outreach_approval_<date>.csv`: high-score leads for manual review
- `agency_pipeline_runbook_<date>.md`: daily operating notes and top candidates

## Low-Cost Mode

Default mode uses:

- the built-in public agency seed list
- public agency websites
- opportunistic DuckDuckGo HTML search when it is not blocked
- optional Brave Search, Serper, Tavily, Exa, SerpAPI, or Google Programmable Search for API-backed discovery
- optional CSV import from Apollo/Sales Navigator/manual lists
- deterministic scoring

No paid API is required.

Useful commands:

```powershell
python ops\prospecting\build_agency_pipeline.py --dry-run
python ops\prospecting\discover_agencies.py --dry-run
python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 50 --min-score 45
python ops\prospecting\discover_agencies.py --source brave --segment b2b-lead-gen --country "United States" --max-queries 20
python ops\prospecting\discover_agencies.py --source serper --segment b2b-lead-gen --country "United States" --max-queries 20
python ops\prospecting\build_agency_pipeline.py --query-limit 3 --max-sites 20
python ops\prospecting\build_agency_pipeline.py --no-search --seed-file ops\prospecting\agency_seed_urls.example.txt
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30
python ops\prospecting\build_agency_pipeline.py --input-csv path\to\apollo_export.csv
```

If DuckDuckGo returns an anomaly/throttle page, the run still works from seed URLs and CSV imports. For scale after first validation, add a paid search/data source such as Apollo, Clay, SerpAPI, or a sequencing CRM export rather than trying to bypass search-engine protections.

## Optional OpenClaw Enrichment

OpenClaw enrichment is off by default. Enable it only for the best deterministic leads:

```powershell
python ops\prospecting\build_agency_pipeline.py --query-limit 3 --max-sites 30 --openclaw-top-n 5
```

Recommended first model route:

- `github-copilot/gpt-5.3-codex` through OpenClaw/Copilot sign-in when available
- fallback to `openai-codex/gpt-5.2-codex` if Copilot is unavailable or quota-constrained
- no API-key model by default

Keep `--openclaw-top-n` low until outreach reply quality proves the angle. The agent receives a compact evidence payload and must return strict JSON. It should not browse broadly, invent facts, send messages, or own pipeline state.

## Manual Review Rules

Before outreach:

- verify the agency is real and fits the ICP
- verify the decision-maker manually on LinkedIn or the agency website
- verify any email source
- check the opener against the visible evidence
- add opt-out language before email sending

First CTA:

> Open to me sending 2-3 specific automation ideas for your agency?

## Contact + Pitch Pack Stage

After generating `agency_outreach_approval_<date>.csv`, run the contact and pitch-pack stage:

```powershell
python ops\prospecting\enrich_agency_contacts.py --max-accounts 10 --max-contact-queries 4
```

This writes clean manual-review outputs under `data/prospects/`:

- `agency_contacts_<date>.csv`: one row per public contact candidate, with source URL, confidence, and verification status.
- `agency_pitch_pack_<date>.csv`: one row per account, with best contact, LinkedIn touch, cold email, follow-up, Loom plan, assumptions, and do-not-claim guardrails.
- `agency_contact_pitch_review_<date>.md`: skim-friendly review file for the top accounts.

OpenClaw pitch refinement is optional and should stay capped:

```powershell
python ops\prospecting\enrich_agency_contacts.py --max-accounts 10 --openclaw-top-n 3 --openclaw-command C:\Users\athar\AppData\Roaming\npm\openclaw.cmd
```

Do not send directly from these files. Use them to manually verify contact identity, source URLs, email deliverability, and final copy.

## Why This Shape

The source of truth stays in CSV/CRM state, not inside an agent. Python owns discovery, dedupe, scoring, and state. AI is reserved for research and personalization where it gives leverage. This keeps costs and failure modes controlled while still removing manual internet scouring.
