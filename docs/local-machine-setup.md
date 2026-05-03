# Local Machine Setup

## Goal

Run Aperture on your laptop for early validation while keeping it separate from your normal work.

## What is separated

- Aperture has its own project `.env`
- Aperture has its own OpenClaw config at [openclaw/local/aperture.local.json5](C:\CS\Agency\Aperture\openclaw\local\aperture.local.json5)
- Aperture has its own OpenClaw state dir at [openclaw/state/local](C:\CS\Agency\Aperture\openclaw\state\local)
- Aperture has its own OpenClaw workspaces under [openclaw/workspaces](C:\CS\Agency\Aperture\openclaw\workspaces)
- Aperture has its own startup scripts under [ops/windows](C:\CS\Agency\Aperture\ops\windows)

This keeps the runtime configuration, agent workspaces, and OpenClaw local state separate from your personal setup.
The app will read the Aperture OpenClaw config and state dir, not the defaults used by your personal setup.

The local Aperture OpenClaw config is gitignored because onboarding writes auth/runtime metadata into it. The sanitized reference file is [openclaw.json5.example](C:\CS\Agency\Aperture\openclaw\openclaw.json5.example).

## How it differs from your personal OpenClaw

- Personal OpenClaw still uses your default home config and state under your user profile.
- Aperture uses [aperture.local.json5](C:\CS\Agency\Aperture\openclaw\local\aperture.local.json5) and [openclaw/state/local](C:\CS\Agency\Aperture\openclaw\state\local).
- Aperture agents are named `lead-enrichment`, `contact-discovery`, `site-audit`, `draft-email`, `draft-whatsapp`, and `reply-classifier`.
- Aperture workspaces live under [openclaw/workspaces](C:\CS\Agency\Aperture\openclaw\workspaces), so you can tell at a glance when you are in the company runtime.

## Files created for local use

- [\.env](C:\CS\Agency\Aperture\.env)
- [bootstrap-local.ps1](C:\CS\Agency\Aperture\ops\windows\bootstrap-local.ps1)
- [setup-openclaw.ps1](C:\CS\Agency\Aperture\ops\windows\setup-openclaw.ps1)
- [start-api.ps1](C:\CS\Agency\Aperture\ops\windows\start-api.ps1)
- [start-worker.ps1](C:\CS\Agency\Aperture\ops\windows\start-worker.ps1)
- [probe-openclaw.ps1](C:\CS\Agency\Aperture\ops\windows\probe-openclaw.ps1)

## First run

From PowerShell in the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\bootstrap-local.ps1
```

This will:
- start Postgres and Redis in Docker
- bind them to local ports `5433` and `6380` so they do not collide with existing services on your machine
- create a Python virtual environment under `backend\.venv`
- install Aperture and dev dependencies
- run Alembic migrations

## Start the stack

Open three terminals.

Terminal 1:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\probe-openclaw.ps1
```

If Aperture has not been logged in yet, run this once first:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\setup-openclaw.ps1
```

That script uses the Aperture-specific config and state dir, runs Codex OAuth, runs the Copilot device login, and then sets `openai-codex/gpt-5.4` as the default model for the company runtime.

Terminal 2:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start-api.ps1
```

Terminal 3:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start-worker.ps1
```

Optional Terminal 4 for continuous discovery + enrichment + draft generation:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\windows\start-pipeline-loop.ps1
```

## Important laptop settings

If you want Aperture to keep running:
- keep the laptop plugged in
- disable sleep while plugged in
- keep Docker Desktop running
- keep the API and worker terminals open

## What you still need to fill in

Before real provider usage, add only the provider values you actually plan to use to [\.env](C:\CS\Agency\Aperture\.env):
- SES credentials when production email sending is enabled
- WhatsApp provider credentials only after explicit compliance checks
- outreach domain
- Google Places API key only if you revive local SMB/place sourcing later

The full variable list is documented in [provider-setup.md](C:\CS\Agency\Aperture\docs\provider-setup.md).
