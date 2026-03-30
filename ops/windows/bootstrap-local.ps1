$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Script,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Write-Host $Description
    & $Script
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

function Ensure-DockerDesktop {
    $cmdExe = "C:\Windows\System32\cmd.exe"
    & $cmdExe /c "docker info >nul 2>nul"
    if ($LASTEXITCODE -eq 0) {
        return
    }

    $dockerDesktopPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path $dockerDesktopPath)) {
        throw "Docker Desktop is not installed. Install it or start your local Docker daemon first."
    }

    Write-Host "Docker Desktop is not running. Starting it now..."
    Start-Process -FilePath $dockerDesktopPath

    for ($i = 0; $i -lt 24; $i++) {
        Start-Sleep -Seconds 5
        & $cmdExe /c "docker info >nul 2>nul"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Docker Desktop is ready."
            return
        }
    }

    throw "Docker Desktop did not become ready within 120 seconds."
}

function Resolve-PythonExe {
    $candidates = @(
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python313\python.exe",
        "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python312\python.exe",
        "python"
    )

    foreach ($candidate in $candidates) {
        if ($candidate -eq "python") {
            try {
                $versionOutput = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
                if ($LASTEXITCODE -eq 0 -and [version]$versionOutput -ge [version]"3.12") {
                    return "python"
                }
            } catch {
                continue
            }
            continue
        }

        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "Python 3.12+ was not found. Install Python 3.12+ or update ops\\windows\\bootstrap-local.ps1 candidates."
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$backendDir = Join-Path $repoRoot "backend"
$venvDir = Join-Path $backendDir ".venv"
$dockerComposeFile = Join-Path $repoRoot "ops\\docker\\docker-compose.yml"
$alembicIni = Join-Path $repoRoot "alembic.ini"
$pythonBootstrapExe = Resolve-PythonExe

Write-Host "Aperture local bootstrap starting..."
Write-Host "Using Python bootstrap executable:" $pythonBootstrapExe

if (-not (Test-Path (Join-Path $repoRoot ".env"))) {
    throw "Expected .env at $repoRoot\.env"
}

if (-not (Test-Path (Join-Path $repoRoot "openclaw\\local\\aperture.local.json5"))) {
    throw "Expected local OpenClaw config at openclaw\\local\\aperture.local.json5"
}

Ensure-DockerDesktop
Invoke-Checked -Description "Starting local Postgres and Redis via Docker..." -Script {
    docker compose -f $dockerComposeFile up -d
}

if (-not (Test-Path $venvDir)) {
    Invoke-Checked -Description "Creating virtual environment..." -Script {
        & $pythonBootstrapExe -m venv $venvDir
    }
}

$pythonExe = Join-Path $venvDir "Scripts\\python.exe"

Invoke-Checked -Description "Installing Aperture dependencies..." -Script {
    & $pythonExe -m pip install --upgrade pip
}

Invoke-Checked -Description "Installing project package..." -Script {
    & $pythonExe -m pip install -e "$repoRoot[dev]"
}

Push-Location $repoRoot
try {
    Invoke-Checked -Description "Running database migrations..." -Script {
        & $pythonExe -m alembic -c $alembicIni upgrade head
    }
} finally {
    Pop-Location
}

Write-Host "Bootstrap complete."
Write-Host "Next steps:"
Write-Host "1. Fill in provider keys in .env"
Write-Host "2. Run ops\\windows\\start-api.ps1"
Write-Host "3. Run ops\\windows\\start-worker.ps1"
Write-Host "4. Run ops\\windows\\probe-openclaw.ps1"
