$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$env:OPENCLAW_CONFIG = Join-Path $repoRoot "openclaw\\local\\aperture.local.json5"

Write-Host "Using OpenClaw config:" $env:OPENCLAW_CONFIG
openclaw models status --json
