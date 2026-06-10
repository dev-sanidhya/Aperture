# Agency

## What This Is
Low-cost B2B agency lead pipeline for selling AI workflow implementation to international agencies.
Daily automated pipeline: discover agencies → score for AI ROI → generate outreach batch → founder-led LinkedIn/email.
OpenClaw used only for capped enrichment on best leads. Amazon SES for production email.

The public marketing website is a separate project in the nested `Aperture/` folder (its own git repo, gitignored here). This repo is the lead-generation / outreach pipeline only.

## Stack
- Python 3.11
- FastAPI + SQLAlchemy
- PostgreSQL (production) / SQLite (dev)
- Redis + Dramatiq (background tasks)
- OpenClaw (optional AI enrichment — off by default)
- Amazon SES (email, production only)
- Twilio WhatsApp (only after explicit compliance checks)
- Brave / Serper / Tavily / Exa / SerpAPI (optional web search fanout)
- Docker Compose (local services)
- alembic (migrations)

## Commands
```powershell
# Prospecting pipeline
python ops\prospecting\discover_agencies.py --dry-run
python ops\prospecting\discover_agencies.py --source seed --seed-file ops\prospecting\agency_seed_urls.example.txt --max-results 50 --min-score 45
$today = Get-Date -Format yyyy-MM-dd
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "data\prospects\agency_research_queue_$today.csv" --max-sites 30

# With optional OpenClaw enrichment (top leads only)
python ops\prospecting\build_agency_pipeline.py --no-search --input-csv "..." --max-sites 30 --openclaw-top-n 5

# Start services
docker compose up -d
```

## Architecture
```
backend/          # FastAPI application
  app/
    api/          # API routes
    core/         # Config, db, auth
    models/       # SQLAlchemy models
    services/     # Business logic
ops/
  prospecting/    # Discovery + scoring scripts
    discover_agencies.py
    build_agency_pipeline.py
    agency_seed_urls.example.txt
  .env.example    # Environment template
data/
  prospects/      # Generated CSV files (gitignored)
contracts/        # Client contracts/docs
rules/            # Business rules
openclaw/         # OpenClaw integration
Aperture/         # Marketing website — SEPARATE nested git repo (gitignored here)
```

## Permanent Facts
- OpenClaw enrichment is OFF by default — only enable for top-scoring leads with --openclaw-top-n
- Generated prospect files go to data/prospects/ (gitignored)
- Never enable Twilio WhatsApp without explicit compliance checks
- Use Amazon SES only in production — not for testing
- All API keys in .env — never hardcode
- Min score threshold: 45 (configurable) before outreach generation

## GitHub
https://github.com/wannabeaquant/Aperture

## Git & Commits
- Format: `<type>(<scope>): <short imperative description>`
  - feat(prospecting): ... | fix(scoring): ... | chore(ops): ...
- Every self-contained working change = one commit, pushed immediately. Do not batch — commit and push as each unit completes.

## Session Memory
- Read MEMORY.md at session start.
- On "session end": write summary to MEMORY.md.

## Error Log
- Read ERRORS.md before suggesting approaches.
- Log failures after 2+ attempts to ERRORS.md.
