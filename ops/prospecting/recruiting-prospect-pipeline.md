# Recruiting Prospect Pipeline

## Goal

Build a weekly list of founder-led recruiting/staffing agencies that are likely to pay for an AI-assisted sourcing, outreach, follow-up, CRM, and reporting workflow.

## ICP

- Countries: United States, United Kingdom, Australia
- Company type: recruiting agency, staffing agency, executive search firm
- Target size: 5-50 employees
- Best niches: healthcare, technology, engineering, finance, sales, executive search
- Buyer: founder, CEO, managing director, owner, head of operations, head of recruitment

## Qualification Rules

Keep a prospect when at least three of these are true:

- They operate in a high-ticket recruiting niche.
- Their website shows active jobs, candidate workflows, or employer/client workflows.
- They publish a public business email, phone, or LinkedIn company page.
- They appear founder-led or small enough for direct decision-maker access.
- Their workflow likely involves manual sourcing, outreach, screening, follow-up, or CRM updates.

Reject a prospect when:

- It is a huge enterprise staffing brand.
- It is a solo recruiter with no visible budget signal.
- It is only a job board, directory, or HR blog.
- It has no clear recruiting/staffing business model.
- It targets very low-margin local labor with no specialization.

## List Sources

Use these in order:

1. Public search results for niche recruiting agencies.
2. Agency websites and contact pages.
3. Public recruiting directories and association member lists.
4. LinkedIn manual verification for founder/CEO/MD identity.
5. Email enrichment tools only after the company passes qualification.

Do not scrape LinkedIn aggressively. Use LinkedIn primarily for manual verification and founder-led outreach.

## Data Fields

- `company_name`
- `website`
- `country`
- `niche`
- `public_email`
- `phone`
- `linkedin_url`
- `source_query`
- `source_url`
- `pain_signal`
- `personalized_angle`
- `score`
- `status`
- `notes`

## Daily Workflow

1. Generate or source 50-100 candidate companies.
2. Keep the top 25-40 after qualification.
3. Manually verify the best 10-20 on LinkedIn.
4. Add founder/CEO/MD names and LinkedIn URLs.
5. Send a teardown-led message, not a generic pitch.
6. Track replies, calls, objections, and accepted teardown angles.

## Local Build

Run from the repo root:

```powershell
python ops\prospecting\build_recruiting_prospects.py
```

The script reads `ops/prospecting/recruiting_seed_urls.txt` when present. If that file does not exist, it falls back to `ops/prospecting/recruiting_seed_urls.example.txt`.

Generated CSV/XLSX files are written to `data/prospects/`, which is intentionally ignored by Git.

## Outreach CTA

Use this CTA for the first test:

> Want me to send over 2-3 specific places where AI could remove manual sourcing/outreach/admin work from your recruiting workflow?

## First Offer

AI Recruiting Ops Sprint:

- sourcing/enrichment workflow
- outreach personalization workflow
- follow-up workflow
- CRM/ATS update workflow
- candidate/client summary workflow
- SOP and team handoff

Start first pilots at `$1.5k-$3k`, then move to `$5k-$10k` once proof exists.

## Existing Aperture Reuse

Reusable:

- lead normalization and dedupe
- source records and evidence packs
- contact discovery
- site audit
- draft generation
- campaign state, suppression, send caps, and reply classification

Needs changing:

- India-local SMB categories should become international recruiting/staffing segments.
- Website-funnel pitch should become AI recruiting ops/workflow pitch.
- Google Maps sourcing should become search/directories/Sales Navigator/manual verification.
- Gmail one-off sending should become domain-authenticated sequencing via Instantly, Smartlead, or SES.
