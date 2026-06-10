# Agency - Plan

## What this repo is
The B2B agency lead-generation and outreach pipeline (FastAPI + Postgres + Redis + Dramatiq + OpenClaw).
Discovers agencies, scores them for AI-ROI fit, and generates founder-led outreach batches.

The marketing website was split out on 2026-06-10 into the nested `Aperture/` folder, which is now its
own git repo with its own memory. Nothing in this repo touches the website anymore.

## Pipeline (high level)
1. `ops/prospecting/discover_agencies.py` - discover candidate agencies (seed list or web-search fanout).
2. `ops/prospecting/build_agency_pipeline.py` - score sites, optional capped OpenClaw enrichment on top leads.
3. Outreach batch generation - founder-led LinkedIn / email (Amazon SES in production only).

## Key constraints
- OpenClaw enrichment OFF by default; only `--openclaw-top-n` for top leads.
- Min score threshold 45 before outreach generation.
- Twilio WhatsApp only after explicit compliance checks.
- Amazon SES only in production, never for testing.
- Generated prospect CSVs go to `data/prospects/` (gitignored).

## Next steps
<!-- Updated each session -->
