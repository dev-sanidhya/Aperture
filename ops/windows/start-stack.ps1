$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$powershellExe = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

Start-Process $powershellExe -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\probe-openclaw.ps1`""
Start-Process $powershellExe -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\start-api.ps1`""
Start-Process $powershellExe -ArgumentList "-ExecutionPolicy Bypass -File `"$repoRoot\ops\windows\start-worker.ps1`""

Write-Host "Started OpenClaw probe, API, and worker in separate PowerShell windows."
