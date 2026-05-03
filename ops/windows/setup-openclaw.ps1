$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$env:OPENCLAW_CONFIG_PATH = Join-Path $repoRoot "openclaw\\local\\aperture.local.json5"
$env:OPENCLAW_STATE_DIR = Join-Path $repoRoot "openclaw\\state\\local"

New-Item -ItemType Directory -Force -Path $env:OPENCLAW_STATE_DIR | Out-Null

Write-Host "Aperture OpenClaw setup"
Write-Host "Config:" $env:OPENCLAW_CONFIG_PATH
Write-Host "State dir:" $env:OPENCLAW_STATE_DIR
Write-Host ""
Write-Host "This keeps Aperture separate from your personal OpenClaw state."
Write-Host "Complete the login flow in this window."
Write-Host ""

openclaw config file
openclaw onboard --auth-choice openai-codex
openclaw models auth login --provider openai-codex
openclaw models auth login-github-copilot
openclaw models set openai-codex/gpt-5.4
openclaw models status --json
