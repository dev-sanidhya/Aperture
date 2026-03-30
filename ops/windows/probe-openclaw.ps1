$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$openclawExe = Join-Path $repoRoot ".openclaw-cli\\node_modules\\.bin\\openclaw.cmd"
$configPath = Join-Path $repoRoot "openclaw\\local\\aperture.local.json5"
$env:OPENCLAW_CONFIG_PATH = $configPath
$env:OPENCLAW_CONFIG = $configPath

Write-Host "Using OpenClaw config:" $env:OPENCLAW_CONFIG_PATH
Write-Host "Using OpenClaw CLI:" $openclawExe
& $openclawExe models status --json
