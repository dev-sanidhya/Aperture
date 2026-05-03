# Dedicated OpenClaw Hosting

OpenClaw is optional for the first B2B agency prospecting motion. The deterministic pipeline can run without it.

Use OpenClaw only for capped enrichment on leads that have already passed deterministic scoring. Do not let an agent own discovery, dedupe, sender state, suppression, or outreach sending.

## Recommended Shape

- local OpenClaw during first validation
- one dedicated VPS later for the Aperture app stack
- OpenClaw installed on that VPS as a separate service user
- separate OpenClaw config, auth state, channels, and logs from any personal setup

## Why

- isolates customer outreach from personal sessions and channels
- makes provider health and auth state predictable
- lets you rotate Codex or Copilot auth without touching your personal assistant
- keeps outreach channels scoped to the agency runtime
- keeps model spend bounded by explicit pipeline flags such as `--openclaw-top-n`

## Local Startup Setup

Use this only when you want optional AI enrichment:

```bash
openclaw onboard --auth-choice openai-codex
openclaw models auth login --provider openai-codex
openclaw models auth login --provider github-copilot
```

Recommended first route:

- primary: `github-copilot/gpt-5.3-codex`
- fallback: `openai-codex/gpt-5.2-codex`
- thinking: `low`
- top-lead cap: 5-10 leads per run

Do not use unofficial ChatGPT web automation as production infrastructure. If subscription-backed OpenClaw routes are configured and allowed by the providers, keep them quota-limited and separate from outreach sending.

## VPS Setup Later

1. Create a dedicated UNIX user such as `aperture`.
2. Install Node 22+ and `openclaw`.
3. Store runtime config under `/home/aperture/.openclaw/`.
4. Run the OpenClaw onboarding commands above.
5. Install the Gateway daemon or run it under `systemd`.

## Aperture App Config

Set:

- `APERTURE_OPENCLAW_COMMAND=openclaw`
- `APERTURE_OPENCLAW_CONFIG=/home/aperture/.openclaw/openclaw.json`
- `APERTURE_OPENCLAW_HOST_LABEL=agency-openclaw-vps`

The backend will treat this host runtime as the agency OpenClaw instance.

## Prospecting Usage

Default run, no model spend:

```powershell
python ops\prospecting\build_agency_pipeline.py --query-limit 3 --max-sites 30
```

Capped enrichment run:

```powershell
python ops\prospecting\build_agency_pipeline.py --query-limit 3 --max-sites 30 --openclaw-top-n 5 --openclaw-thinking low
```
