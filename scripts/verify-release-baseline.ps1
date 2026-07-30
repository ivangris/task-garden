param(
  [switch]$SkipE2E,
  [switch]$SeedDemo,
  [switch]$Hosted
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$python = Join-Path $apiRoot ".venv\Scripts\python.exe"
$alembic = Join-Path $apiRoot ".venv\Scripts\alembic.exe"
$minimumNodeVersion = [version]"22.19.0"

function Invoke-Checked {
  param(
    [string]$Label,
    [scriptblock]$Command
  )

  Write-Host "`n==> $Label" -ForegroundColor Cyan
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE."
  }
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
  throw "Backend virtualenv is missing at $python."
}

if (-not (Test-Path -LiteralPath $alembic -PathType Leaf)) {
  throw "Alembic is missing at $alembic."
}

$nodeVersionText = (& node --version).Trim().TrimStart("v")
$nodeVersion = [version]$nodeVersionText
if ($nodeVersion -lt $minimumNodeVersion) {
  throw "Node $minimumNodeVersion or newer is required. Found $nodeVersion."
}

Push-Location $repoRoot
try {
  Invoke-Checked "Backend tests" {
    & $python -m unittest discover -s apps\api\tests
  }
  Invoke-Checked "Frontend typecheck" {
    npm.cmd run typecheck:web
  }
  Invoke-Checked "Frontend production build" {
    npm.cmd run build:web
  }
  Invoke-Checked "Garden asset validation" {
    npm.cmd run check:garden-assets
  }

  $migrationRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("task-garden-baseline-" + [guid]::NewGuid().ToString("N"))
  New-Item -ItemType Directory -Path $migrationRoot | Out-Null
  $migrationDb = Join-Path $migrationRoot "migration-check.db"
  $previousDatabaseUrl = $env:TASK_GARDEN_DATABASE_URL
  try {
    $migrationPath = $migrationDb.Replace("\", "/")
    $env:TASK_GARDEN_DATABASE_URL = "sqlite:///$migrationPath"
    Push-Location $apiRoot
    try {
      Invoke-Checked "Fresh SQLite migration" {
        & $alembic upgrade head
      }
    } finally {
      Pop-Location
    }
  } finally {
    $env:TASK_GARDEN_DATABASE_URL = $previousDatabaseUrl
    Remove-Item -LiteralPath $migrationRoot -Recurse -Force
  }

  if (-not $SkipE2E) {
    Invoke-Checked "Playwright smoke tests" {
      npm.cmd run qa:e2e
    }
  }

  if ($SeedDemo) {
    Invoke-Checked "Demo data reset and seed" {
      npm.cmd run seed:demo -- --reset
    }
  }

  if ($Hosted) {
    Invoke-Checked "Hosted Docker/Postgres rehearsal" {
      powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hosted-rehearsal.ps1 -Reset
    }
  }

  Write-Host "`nTask Garden release baseline passed." -ForegroundColor Green
} finally {
  Pop-Location
}
