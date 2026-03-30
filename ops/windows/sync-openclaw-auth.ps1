$ErrorActionPreference = "Stop"

$agentIds = @(
    "lead-enrichment",
    "contact-discovery",
    "site-audit",
    "draft-email",
    "draft-whatsapp",
    "reply-classifier"
)

$sourceAuth = Join-Path $env:USERPROFILE ".openclaw\\agents\\main\\agent\\auth-profiles.json"
if (-not (Test-Path $sourceAuth)) {
    throw "Source auth profile not found at $sourceAuth. Complete the main OpenClaw login first."
}

foreach ($agentId in $agentIds) {
    $targetDir = Join-Path $env:USERPROFILE ".openclaw\\agents\\$agentId\\agent"
    $targetAuth = Join-Path $targetDir "auth-profiles.json"
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
    Copy-Item -Path $sourceAuth -Destination $targetAuth -Force
    Write-Host "Synced auth profile to $targetAuth"
}

Write-Host "OpenClaw auth sync complete."
