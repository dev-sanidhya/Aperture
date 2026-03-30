$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendDir = Join-Path $repoRoot "backend"
$pythonExe = Join-Path $backendDir ".venv\\Scripts\\python.exe"

if (-not (Test-Path $pythonExe)) {
    throw "Virtual environment not found. Run ops\\windows\\bootstrap-local.ps1 first."
}

Set-Location $repoRoot
$env:PYTHONPATH = $backendDir
& $pythonExe -m dramatiq app.workers.tasks
