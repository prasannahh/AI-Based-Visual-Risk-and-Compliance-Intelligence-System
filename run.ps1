# run.ps1
# Launches the linked Digital Twin AI app: Milestone 1 Streamlit UI + the
# Milestone 2 AI Core Layer (imported via ai_bridge.py). Both share the
# `digital_twin` PostgreSQL database.
#
# Usage:
#   .\run.ps1
#
# Shortcut:
#   python run.py

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appDir = Join-Path $projectRoot "Mile stone 1\AI-Driven-Digital-Twin-Solutions-main\AI-Driven-Digital-Twin-Solutions-main"
$aiCore = Join-Path $projectRoot "Milestone 2\ai_models"

if (-not (Test-Path -LiteralPath $appDir)) {
    Write-Error "Milestone 1 app not found: $appDir"
    exit 1
}
if (-not (Test-Path -LiteralPath $aiCore)) {
    Write-Error "Milestone 2 AI core not found: $aiCore"
    exit 1
}

Write-Host "Starting Digital Twin AI from: $appDir"
Write-Host "AI Core Layer (Milestone 2):  $aiCore"
Write-Host "Database: digital_twin (configure in .streamlit/secrets.toml)"

Set-Location -LiteralPath $appDir
python -m streamlit run app.py
