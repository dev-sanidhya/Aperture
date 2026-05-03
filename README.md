# Aperture

Aperture is a low-cost B2B agency lead pipeline for selling practical AI workflow implementation to international agencies.

The first motion is simple:

1. Build a daily list of B2B agencies from seed URLs, optional public search, and optional CSV imports.
2. Score them for likely AI workflow ROI.
3. Generate a manual approval batch for founder-led LinkedIn/email outreach.
4. Use OpenClaw only for capped enrichment on the best leads.

## Stack

- FastAPI
- PostgreSQL
- Redis + Dramatiq
- OpenClaw for optional enrichment and drafting
- Amazon SES when production email sending is enabled
- Twilio WhatsApp only after explicit compliance checks

## Prospecting Quick Start

Run from the repo root:

```powershell
python ops\prospecting\discover_agencies.py --dry-run
python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 50 --min-score 45
python ops\prospecting\build_agency_pipeline.py --dry-run
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30
```

Generated prospect files are written to ignored `data/prospects/`.

API-backed discovery is optional. Configure Brave, Serper, Tavily, Exa, SerpAPI, or Google Programmable Search keys in `.env` when you want automated web-search fanout.

OpenClaw enrichment is off by default. Use it only for the best deterministic leads:

```powershell
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30 --openclaw-top-n 5
```

The operating runbook is in [ops/prospecting/agency-lead-pipeline.md](ops/prospecting/agency-lead-pipeline.md).

## App Setup

1. Copy `ops/.env.example` to `.env`.
2. Update only the provider credentials you actually have.
3. Start the local services with Docker Compose.
4. Run `openclaw` onboarding only if you want optional AI enrichment.
5. Start the API and worker processes when using the backend.

Detailed setup is in [docs/setup.md](docs/setup.md).
