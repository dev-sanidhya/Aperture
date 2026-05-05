## 1) Task

- Title: Expand public agency directory importers
- Owner: Codex
- Date: 2026-05-05
- Scope: Add more low-cost public directory sources to the agency importer, keep generated outputs under data/prospects, and identify outreach-ready files.
- Out of scope: Sending outreach, scraping private/member-only surfaces, paid enrichment APIs beyond existing local config.

## 2) Implementation Decisions

- Final approach: Extend ops/prospecting/import_agency_directories.py with source-specific importers that output the existing directory CSV schema.
- Alternatives considered: Use Serper for all expansion; rejected because user wants free/public lists first.
- Dependencies impacted: ops prospecting scripts and docs only.

## 3) Acceptance Criteria

- [x] Importer supports additional public directory sources beyond AgencyReview/AgencySort.
- [x] Output CSV remains compatible with build_agency_pipeline.py.
- [x] Script has timeout/error handling and source caps.
- [x] Outreach-ready files are clearly named for current manual use.

## 4) Verification Commands

### Scripts

- [x] python -m py_compile ops\prospecting\import_agency_directories.py
- [x] Small smoke check with capped profiles/pages.

## 5) Completion Record

- Summary of changes: Added AgencyLoft sitemap/profile import, HubSpot Solutions public search import, and Clutch profile sitemap import, preserving the existing directory CSV schema.
- Known risks: Clutch and DesignRush profile/category pages are Cloudflare-blocked from direct script fetches; Clutch sitemap rows need later website resolution.
- Follow-ups: Add a website resolver for `needs_website` directory rows using Serper or another search provider once we want to convert sitemap-only rows into research-ready website seeds.
