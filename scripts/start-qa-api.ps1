$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $repoRoot "apps\api"
$dataDir = Join-Path $repoRoot "data\sqlite"
$dbPath = Join-Path $dataDir "task-garden-qa.db"
$backupDir = Join-Path $repoRoot "data\backups\qa"
$venvPython = Join-Path $apiRoot ".venv\Scripts\python.exe"
$port = if ($env:TASK_GARDEN_QA_API_PORT) { $env:TASK_GARDEN_QA_API_PORT } else { "18000" }

if (-not (Test-Path $venvPython)) {
  throw "Backend virtualenv missing at $venvPython. Run API setup before QA."
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if ($env:TASK_GARDEN_QA_RESET_DB -ne "0" -and (Test-Path $dbPath)) {
  Remove-Item -LiteralPath $dbPath -Force
}

if ($env:TASK_GARDEN_QA_RESET_DB -ne "0" -and (Test-Path $backupDir)) {
  Remove-Item -LiteralPath $backupDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

$dbUrlPath = $dbPath.Replace("\", "/")
$env:TASK_GARDEN_DATABASE_URL = "sqlite:///$dbUrlPath"
$env:TASK_GARDEN_BACKUP_DIRECTORY = $backupDir.Replace("\", "/")
$env:TASK_GARDEN_TASK_EXTRACTION_PROVIDER = "mock"
$env:TASK_GARDEN_RECAP_NARRATIVE_PROVIDER = "mock"
$env:TASK_GARDEN_STT_PROVIDER = "local_stub"
$env:TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS = "false"
$env:TASK_GARDEN_AUDIO_STORAGE_DIR = (Join-Path $repoRoot "data\audio\qa").Replace("\", "/")

Push-Location $apiRoot
try {
  & $venvPython -m alembic upgrade head
  & $venvPython -m uvicorn app.main:app --host 127.0.0.1 --port $port
} finally {
  Pop-Location
}
