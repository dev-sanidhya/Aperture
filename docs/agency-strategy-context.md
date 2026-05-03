# Agency Strategy Context

This file is the handoff context for future chats about the agency direction, outreach, and prospecting motion. Read this before changing positioning, prospecting, outreach copy, or business strategy.

## Current Direction

Aperture is being repositioned from a generic automated agency into an AI recruiting ops implementation agency.

The target business is:

> AI-assisted recruiting operations systems for founder-led recruiting/staffing agencies.

The practical offer is not "AI agency", "websites", or "marketing". Those are implementation details. The external offer is a workflow system that helps recruiting teams reduce repetitive manual work and create more candidate/client conversations.

## Target ICP

- Geography: United States, United Kingdom, Australia
- Company type: recruiting agency, staffing agency, executive search firm
- Size: roughly 5-50 employees
- Buyer: founder, CEO, managing director, owner, head of operations, head of recruitment
- Best niches: healthcare, technology, engineering, finance, sales recruitment, executive search
- Avoid initially: generic local SMBs, huge enterprise staffing brands, low-margin local labor agencies, job boards, directories, solo recruiters without budget signal

## Offer

Initial wedge:

> AI Recruiting Ops Sprint

Typical workflow components:

- sourcing/enrichment workflow
- outreach personalization workflow
- follow-up workflow
- CRM/ATS update workflow
- candidate/client summary workflow
- SOP and team handoff

Early pilot pricing:

- First pilots: `$1.5k-$3k`
- Standard sprint after proof: `$5k-$10k`
- Potential retainer after trust: `$1k-$3k/month`

## Positioning

Use:

> We build AI-assisted recruiting ops systems that remove repetitive sourcing/outreach/admin work while keeping recruiters focused on candidate and client conversations.

Do not lead with:

- generic AI automation
- websites
- marketing services
- decks
- "agents" as the main pitch
- unrealistic metrics or unearned case studies

## Outreach Motion

Use a manual, founder-led, teardown-first motion.

Preferred channel order:

1. LinkedIn personal account for trust and conversations
2. Email for follow-up and scale
3. X only as authority/content support if the audience is active there
4. Agency website/page as credibility layer, not the primary acquisition engine

First CTA:

> Want me to send over 2-3 specific places where AI could remove manual sourcing/outreach/admin work from your recruiting workflow?

Do not mass blast unverified seed lists. Verify company fit, decision maker, contact, and copy first.

## Current Prospecting Assets

Tracked workflow files:

- `ops/prospecting/build_recruiting_prospects.py`
- `ops/prospecting/recruiting-prospect-pipeline.md`
- `ops/prospecting/recruiting_seed_urls.example.txt`

Generated local files are intentionally ignored under `data/prospects/`.

As of 2026-05-02, the local generated outreach assets were:

- `data/prospects/recruiting_prospects_2026-05-02.csv`
- `data/prospects/outreach_batch_recruiting_2026-05-02.csv`
- `data/prospects/send_ready_recruiting_batch_2026-05-02.csv`
- `data/prospects/manual_outreach_runbook_2026-05-02.md`

These generated files may not exist in a fresh clone because `data/` is ignored. Regenerate prospects with:

```powershell
python ops\prospecting\build_recruiting_prospects.py
```

## Send-Ready Batch Status

A first 10-prospect manual-review batch was prepared locally on 2026-05-02.

Ready after manual review:

- Medfuture Healthcare
- RADAAS
- Evolve Talent
- RCS Staffing
- GHS Recruiting
- HCRC Staffing
- K & K Technical Group
- Infotech Staffing

Not ready without more contact research:

- Fifthhost Consulting
- Agility Health

No outreach was sent by the agent.

## Sending Rules

Before sending commercial cold email, require:

- confirmed sender account
- physical mailing address for commercial email footer
- opt-out language
- final approval of exact recipients and copy
- public business contact or verified decision-maker contact

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

- India-local SMB category sourcing should become international recruiting/staffing account sourcing.
- Website-funnel pitch should become AI recruiting ops/workflow pitch.
- Google Maps sourcing should be supplemented or replaced with public search, directories, Sales Navigator/manual verification, and compliant enrichment providers.
- Gmail one-off sending should not become production infrastructure; use authenticated sender tooling such as SES, Instantly, Smartlead, or another proper sequencing provider.

## Near-Term Plan

1. Manually verify the first 10 prospects.
2. Fill decision-maker name, title, LinkedIn, email, source URLs, and confidence.
3. Send only approved LinkedIn/email touches.
4. Track every touch and reply in the outreach CSV or CRM.
5. If replies ask for more detail, send a short workflow teardown, not a deck.
6. Sell a contained pilot sprint before proposing a retainer.

## Operating Principle

The goal is signal, not volume.

Do not scale outreach until reply quality, objection patterns, and at least one paid pilot validate the niche and offer.
