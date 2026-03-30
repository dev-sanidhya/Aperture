$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\probe-openclaw.ps1`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\start-api.ps1`""
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\start-worker.ps1`""

Write-Host "Started OpenClaw probe, API, and worker in separate PowerShell windows."
