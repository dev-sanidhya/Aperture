# Agency - Plan

## What this repo is
The B2B agency lead-generation and outreach pipeline (FastAPI + Postgres + Redis + Dramatiq + OpenClaw).
Discovers agencies, scores them for AI-ROI fit, and generates founder-led outreach batches.

The marketing website was split out on 2026-06-10 into the nested `Aperture/` folder, which is now its
own git repo with its own memory. Nothing in this repo touches the website anymore.

## Clients
- **PriBhum Nest** (first agency client). Lives under `PriBhum Nest/` as two nested client git repos
  (gitignored here): `Mobile/` (github.com/wannabeaquant/pribhum-nest - Expo app + Supabase admin panel,
  Supabase phone/SMS OTP) and `Website/` (github.com/RajatMawal/PG-WEB - MERN PG-listing site with
  email OTP, JWT/Google auth).
  - 2026-06-22: Cloned both. On the Website repo, resolved leftover merge-conflict markers that were
    breaking the build (otpController, propertyController, Server.js), moved `redux/` into `src/`, and
    confirmed the existing email-OTP flow (register verification + forgot-password) is wired correctly -
    matching mobile's conceptual flow with minimum effort per client request. Work sits on the
    `feat/otp-flow-and-structure` branch in that repo; not pushed to the client remote yet.

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

## Lower-tier cold-call lead scrape (2026-06-22)
Goal: scrape NET-NEW lower-tier leads (weak/no website, modest reviews, but earning -- the opposite
of the established tier-2 firms in the user's existing `vapi_contacts.csv` / `india_call_list_personalized.csv`).
Targets: 200 US roofing (voice agent), 100 India interior, 150 India aesthetic clinics.
- Tool: Apify `compass/crawler-google-places` (Google Maps Scraper). User's OWN Apify token (FREE plan,
  $5/mo hard cap) -- this is the binding constraint, not actor choice. ~$5 per 1,000 places.
- Strategy: search smaller suburbs/localities (so small operators rank top, not the giants).
- User decisions: India market for interior+clinics; same 4 metros for roofing (deduped); Maps number +
  E.164 format check (no carrier validation); STRICT low-tier = weak/no/http website ONLY, partial counts
  accepted (won't blow the $5 cap to hit full targets).
- Scripts (ops/prospecting/): `scrape_lower_tier.py` (initial), `scrape_gaps.py` (curl run-sync gap fill),
  `consolidate_recover.py` (classify Apify datasets by searchString -> raw buckets),
  `build_lists.py` (strict filter + phone validation + dedup vs existing -> final CSVs).
- Gotchas hit: FREE 8GB memory cap (async runs orphaned by a dead poller piled up -> 402); Python urllib
  timeouts in this env (use curl instead); Windows cp1252 decode bug on UTF-8 names (fetch via `curl -o`,
  not Python text mode). Apify keeps every run's dataset server-side, so partial/failed local saves are
  always recoverable by re-fetching the dataset id.
- RESULT after India top-up (`scrape_more_india.py`, fresh BLR/DEL/GGN localities; usage ~$4.46 of $5):
  us_roofing_lower_tier.csv = 97, india_interior_lower_tier.csv = 67, india_aesthetic_clinics_lower_tier.csv = 36.
  All E.164-valid, unique, 0 overlap with existing lists. Budget now effectively exhausted ($0.54 left).
  Clinics inherently low yield under strict filter (Indian clinics nearly all have own sites).
- Clinic budget-max pass (`clinic_blast.py` + cheap actor `S3TUPOWUK8RoocPjh` @ $1/1k via
  `normalize_cheap.py`): premium actor blocked once remaining < its per-run reservation, so switched to
  the $1/1k actor for the last cents. CONFIRMED the FREE cap is a hard $5 (not $7) -- Apify error
  `not-enough-usage-to-run-paid-actor`. Usage maxed at ~$4.97/$5.
- FINAL counts: us_roofing_lower_tier.csv = 96, india_interior_lower_tier.csv = 67,
  india_aesthetic_clinics_lower_tier.csv = 42 (now spans BLR/DEL/GGN + Pune/Noida/Mumbai). 205 total,
  all E.164-valid, unique, 0 overlap with existing lists.
- To go further: FREE $5/mo is fully spent -> user must raise the Apify cap / use a funded token.
  Free rebuild/re-tune from already-paid Apify datasets: re-fetch dataset ids -> consolidate_recover.py
  (+ normalize_cheap.py for cheap-actor data) -> build_lists.py. Loosen is_lower_tier() for more volume.

## Next steps
<!-- Updated each session -->
