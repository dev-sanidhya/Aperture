# Agency Strategy Context

This file is the handoff context for future chats about the agency direction, outreach, and prospecting motion. Read this before changing positioning, prospecting, outreach copy, or business strategy.

## Current Direction

Aperture is being repositioned from a recruiting-only prospecting setup into a B2B agency lead pipeline for selling practical AI workflow implementation.

The target business is:

> AI workflow systems for B2B agencies that are losing time on manual lead intake, client reporting, proposal drafting, CRM updates, research, and delivery handoffs.

The external offer is not "AI agency", "agents", or "automation". Those are implementation details. The client-facing promise is a contained workflow sprint that saves team hours, improves follow-up speed, and gives agency operators more delivery capacity.

## Target ICP

- Geography: United States, United Kingdom, Canada, Australia
- Company type: B2B lead-generation, growth, paid media, SEO, HubSpot/RevOps, recruiting/staffing, product/dev, or specialist marketing agencies
- Size: roughly 10-50 employees, with room to test 5-100
- Buyer: founder, CEO, managing director, COO, head of client services, head of operations, head of RevOps, head of recruitment
- Best initial segments: B2B lead-generation/growth agencies, paid media or SEO agencies serving SaaS/B2B clients, HubSpot/RevOps agencies, and recruiting/staffing agencies as a sub-segment
- Avoid initially: random local SMBs, huge enterprises, directories, agencies without B2B client signal, agencies with no visible service complexity, and solo operators without budget signal

## Offer

Initial wedge:

> AI Workflow Sprint for B2B Agencies

Typical workflow components:

- call transcript to CRM notes, follow-up, proposal outline, and internal tasks
- lead intake to enrichment, qualification, CRM update, and follow-up drafts
- campaign/reporting data to client-ready insights and account-manager drafts
- client intake to project brief, tasks, owners, and handoff updates
- recruiting notes to candidate/client summaries, shortlists, outreach drafts, follow-ups, and ATS updates

Early pilot pricing:

- First pilots: `$1.5k-$3k`
- Standard sprint after proof: `$3k-$7.5k`
- Larger workflow/dashboard sprint after proof: `$7.5k-$15k`
- Potential retainer after trust: `$750-$2k/month`

## Positioning

Use:

> We build practical AI workflows for B2B agencies that turn calls, briefs, reports, and lead forms into follow-ups, CRM updates, proposals, tasks, and client-ready insights.

Short version:

> We help B2B agencies remove manual ops from lead intake, reporting, proposals, CRM updates, and delivery handoffs.

Do not lead with:

- generic AI automation
- websites
- chatbots
- "agents" as the main pitch
- unrealistic metrics or unearned case studies
- fully autonomous outbound claims

## Outreach Motion

Use a founder-led, teardown-first motion.

Preferred channel order:

1. LinkedIn personal account for trust and conversations
2. Email for follow-up and controlled scale
3. Loom teardown for high-fit prospects
4. X only as authority/content support if the audience is active there
5. Agency website/page as credibility layer, not the primary acquisition engine

First CTA:

> Open to me sending 2-3 specific automation ideas for your agency?

Do not mass blast unverified seed lists. Verify company fit, decision maker, contact, and copy first.

## Current Prospecting Assets

Tracked workflow files:

- `ops/prospecting/discover_agencies.py`
- `ops/prospecting/build_agency_pipeline.py`
- `ops/prospecting/agency-lead-pipeline.md`
- `ops/prospecting/agency_discovery_sources.example.txt`
- `ops/prospecting/agency_seed_urls.example.txt`

Generated local files are intentionally ignored under `data/prospects/`.

Regenerate prospects with:

```powershell
python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 50 --min-score 45
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30
```

Run a no-network smoke check with:

```powershell
python ops\prospecting\build_agency_pipeline.py --dry-run
```

## AI Runtime Strategy

The pipeline is not agent-owned. Python owns:

- search/API query execution
- source fanout
- domain extraction
- seed URL loading
- CSV import
- website fetching
- extraction
- dedupe
- deterministic scoring
- approval-batch state

OpenClaw owns optional top-lead enrichment only:

- summarize observed evidence
- identify the likely workflow pain
- recommend the first outreach angle
- flag risks or uncertainty
- return strict JSON

OpenClaw is disabled by default. Use `--openclaw-top-n 5` only after the deterministic list is already scored.

Search is opportunistic, not the only source. Public search engines can throttle HTML results, so the startup pipeline must keep working from the built-in seed list and CSV imports. Add paid search/data APIs only after the first reply or pilot signal justifies spend.

Preferred discovery source order:

1. Seed/list sources for free reproducible runs.
2. Brave Search API or Serper for free/low-cost web-search fanout.
3. Tavily or Exa as free-credit alternatives for AI-search style results.
4. SerpAPI when Google-style result quality is worth the cost.
5. Google Programmable Search when already configured.
6. Apollo/Hunter/Tomba only after reply quality justifies credits.

Recommended startup route:

- Use the existing OpenClaw/Codex setup if it is already authenticated locally.
- Prefer the verified Codex `gpt-5.4` route and Copilot `gpt-5.3-codex` fallback.
- Keep enrichment payloads compact.
- Do not use unofficial ChatGPT web automation to bypass product/API boundaries.
- Do not add Hermes for v1 unless OpenClaw fails in practice.

## Sending Rules

Before sending commercial cold email, require:

- confirmed sender account
- physical mailing address for commercial email footer
- opt-out language
- final approval of exact recipients and copy
- public business contact or verified decision-maker contact
- suppression tracking

Recommended opt-out footer:

> If this is not relevant, reply "no" and I will not follow up.

Do not send cold WhatsApp/text messages unless explicit eligibility, compliance, and suppression handling are in place.

## Existing Aperture Reuse

Useful infrastructure:

- lead normalization and dedupe
- source records and evidence packs
- contact discovery
- site audit
- draft generation
- campaign state
- suppression, send caps, and reply classification
- OpenClaw separation for enrichment/drafting/classification

Needed product pivot:

- India-local SMB category sourcing becomes international B2B agency account sourcing.
- Website-funnel pitch becomes AI workflow implementation pitch.
- Google Maps sourcing becomes public search, seed URLs, optional Apollo/Sales Navigator CSV imports, and compliant enrichment providers later.
- Gmail one-off sending should not become production infrastructure; use authenticated sender tooling such as SES, Instantly, Smartlead, or another proper sequencing provider once sending volume matters.

## Near-Term Plan

1. Generate 30-100 agencies.
2. Manually verify the top 20.
3. Fill decision-maker name, title, LinkedIn, email, source URLs, and confidence.
4. Send LinkedIn-first touches to approved prospects.
5. Record replies and objections in the CSV or CRM.
6. For interested replies, send a short workflow teardown or Loom, not a deck.
7. Sell a contained pilot sprint before proposing a retainer.

## Operating Principle

The goal is signal, not raw volume.

Do not scale outreach until reply quality, objection patterns, and at least one paid pilot validate the niche and offer.
