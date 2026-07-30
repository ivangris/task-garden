param(
  [string]$ProjectName = "task-garden-hosted",
  [string]$Token = "replace-with-a-long-random-token",
  [switch]$Reset
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$composeFile = Join-Path $repoRoot "docker-compose.hosted.example.yml"
$apiBaseUrl = "http://127.0.0.1:18080"

function Assert-NativeSuccess {
  param([string]$Label)
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE."
  }
}

function Invoke-JsonRequest {
  param(
    [string]$Method,
    [string]$Uri,
    [object]$Body = $null,
    [switch]$Authorized
  )

  $headers = @{}
  if ($Authorized) {
    $headers["Authorization"] = "Bearer $Token"
  }

  $params = @{
    Method = $Method
    Uri = $Uri
    Headers = $headers
  }
  if ($null -ne $Body) {
    $params["ContentType"] = "application/json"
    $params["Body"] = ($Body | ConvertTo-Json -Depth 10)
  }

  Invoke-RestMethod @params
}

function Wait-ForApi {
  $deadline = (Get-Date).AddMinutes(2)
  do {
    try {
      $health = Invoke-RestMethod "$apiBaseUrl/health"
      if ($health.status -eq "ok") {
        return
      }
    } catch {
      Start-Sleep -Seconds 2
    }
  } while ((Get-Date) -lt $deadline)

  throw "Hosted API did not become healthy at $apiBaseUrl."
}

Push-Location $repoRoot
try {
  if ($Reset) {
    Write-Output "Resetting hosted rehearsal stack..."
    docker compose -p $ProjectName -f $composeFile down -v
    Assert-NativeSuccess "docker compose down"
  }

  Write-Output "Building hosted API image..."
  docker compose -p $ProjectName -f $composeFile build api
  Assert-NativeSuccess "docker compose build api"

  Write-Output "Starting hosted Postgres..."
  docker compose -p $ProjectName -f $composeFile up -d db
  Assert-NativeSuccess "docker compose up db"

  Write-Output "Waiting for Postgres readiness..."
  docker compose -p $ProjectName -f $composeFile exec -T db sh -c "until pg_isready -U task_garden -d task_garden; do sleep 1; done"
  Assert-NativeSuccess "Postgres readiness check"

  Write-Output "Running Alembic migrations against Postgres..."
  docker compose -p $ProjectName -f $composeFile run --rm api alembic upgrade head
  Assert-NativeSuccess "Postgres Alembic migration"

  Write-Output "Starting hosted API..."
  docker compose -p $ProjectName -f $composeFile up -d api
  Assert-NativeSuccess "docker compose up api"
  Wait-ForApi

  Write-Output "Checking hosted auth and sync contracts..."
  $unauthorized = $null
  try {
    Invoke-JsonRequest -Method Post -Uri "$apiBaseUrl/entries" -Body @{ source_type = "typed"; raw_text = "Blocked hosted write" }
  } catch {
    $unauthorized = $_.Exception.Response.StatusCode.value__
  }
  if ($unauthorized -ne 401) {
    throw "Expected unauthorized hosted write to return 401, got $unauthorized."
  }

  $entry = Invoke-JsonRequest -Method Post -Uri "$apiBaseUrl/entries" -Authorized -Body @{
    source_type = "typed"
    raw_text = "Hosted rehearsal transcript entry"
  }

  $device = Invoke-JsonRequest -Method Post -Uri "$apiBaseUrl/sync/register-device" -Authorized -Body @{
    device_name = "Hosted rehearsal"
    platform = "windows"
    app_version = "phase-10c"
  }

  $pull = Invoke-JsonRequest -Method Get -Uri "$apiBaseUrl/sync/pull?device_id=$($device.id)&cursor=0&limit=20" -Authorized

  $push = Invoke-JsonRequest -Method Post -Uri "$apiBaseUrl/sync/push" -Authorized -Body @{
    device_id = $device.id
    changes = @(
      @{
        event_id = [guid]::NewGuid().ToString()
        entity_type = "raw_entry"
        entity_id = $entry.id
        change_type = "updated"
        changed_at = (Get-Date).ToUniversalTime().ToString("o")
        payload = @{ id = $entry.id; rehearsal = $true }
      }
    )
  }

  [pscustomobject]@{
    health = "ok"
    unauthorized_write_status = $unauthorized
    created_entry_id = $entry.id
    registered_device_id = $device.id
    pulled_change_count = $pull.items.Count
    pushed_change_count = $push.accepted_count
  } | ConvertTo-Json -Depth 5
} finally {
  Pop-Location
}
