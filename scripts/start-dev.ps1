$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\\api"
$webRoot = Join-Path $repoRoot "apps\\web"
$venvPython = Join-Path $apiRoot ".venv\\Scripts\\python.exe"
$venvAlembic = Join-Path $apiRoot ".venv\\Scripts\\alembic.exe"

function Stop-ListenerProcesses {
  param(
    [int[]]$Ports
  )

  $connections = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $Ports -and ($_.LocalAddress -eq "127.0.0.1" -or $_.LocalAddress -eq "::1") } |
    Select-Object -ExpandProperty OwningProcess -Unique

  foreach ($processId in $connections) {
    if (-not $processId) {
      continue
    }

    try {
      $process = Get-Process -Id $processId -ErrorAction Stop
      if ($process.ProcessName -notin @("python", "node")) {
        continue
      }
      Write-Host "Stopping existing listener on PID $processId ($($process.ProcessName))..." -ForegroundColor Yellow
      Stop-Process -Id $processId -Force -ErrorAction Stop
    } catch {
      Write-Host "Could not stop PID $processId. Continuing..." -ForegroundColor DarkYellow
    }
  }
}

if (-not (Test-Path $venvPython)) {
  Write-Host "Backend virtualenv missing. Run the initial setup first." -ForegroundColor Yellow
  exit 1
}

if (-not (Test-Path (Join-Path $repoRoot "node_modules"))) {
  Write-Host "Root node_modules missing. Run npm install first." -ForegroundColor Yellow
  exit 1
}

Write-Host "Stopping previous Task Garden listeners..." -ForegroundColor Cyan
Stop-ListenerProcesses -Ports @(8000, 5173)

Write-Host "Running SQLite migration..." -ForegroundColor Cyan
Push-Location $apiRoot
try {
  & $venvAlembic upgrade head
} finally {
  Pop-Location
}

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
