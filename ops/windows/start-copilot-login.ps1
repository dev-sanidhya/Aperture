$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$configPath = Join-Path $repoRoot "openclaw\local\aperture.local.json5"
$openclawExe = Join-Path $repoRoot ".openclaw-cli\node_modules\.bin\openclaw.cmd"
$command = "`$env:OPENCLAW_CONFIG_PATH='$configPath'; & '$openclawExe' models auth login-github-copilot --yes"

Start-Process -FilePath "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
    -ArgumentList @("-NoExit", "-Command", $command) `
    -WindowStyle Normal

Write-Host "Opened GitHub Copilot login window."
