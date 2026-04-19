$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\\api"
$webRoot = Join-Path $repoRoot "apps\\web"
$venvPython = Join-Path $apiRoot ".venv\\Scripts\\python.exe"
$venvAlembic = Join-Path $apiRoot ".venv\\Scripts\\alembic.exe"

if (-not (Test-Path $venvPython)) {
  Write-Host "Backend virtualenv missing. Run the initial setup first." -ForegroundColor Yellow
  exit 1
}

if (-not (Test-Path (Join-Path $repoRoot "node_modules"))) {
  Write-Host "Root node_modules missing. Run npm install first." -ForegroundColor Yellow
  exit 1
}

Write-Host "Running SQLite migration..." -ForegroundColor Cyan
& $venvAlembic upgrade head

Write-Host "Starting API..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$apiRoot'; & '$venvPython' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

Write-Host "Starting web app..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
  "-NoExit",
  "-Command",
  "Set-Location '$webRoot'; npm run dev -- --host 127.0.0.1 --port 5173"
)

Write-Host "Task Garden launch started." -ForegroundColor Green
Write-Host "API: http://127.0.0.1:8000/health"
Write-Host "Web: http://127.0.0.1:5173/"

