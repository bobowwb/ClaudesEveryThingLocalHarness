param(
  [string]$ProjectRoot = "",
  [string]$MamgaRoot = "C:\AI\MAMGA",
  [int]$MamgaPort = 7788,
  [int]$StartupTimeoutSec = 15,
  [switch]$SkipMamgaStart,
  [switch]$ForCline
)

$ErrorActionPreference = "Continue"

function Get-DefaultProjectRoot {
  $scriptParent = Split-Path -Parent $PSScriptRoot
  if ($scriptParent -and (Test-Path -LiteralPath (Join-Path $scriptParent ".codex\config.toml"))) {
    return $scriptParent
  }
  return (Get-Location).Path
}

function Test-MamgaHealth {
  param([Parameter(Mandatory = $true)][string]$Url)

  try {
    $response = Invoke-RestMethod -Uri $Url -TimeoutSec 2
    return $response.status -eq "ok"
  } catch {
    return $false
  }
}

function Start-Mamga {
  param(
    [Parameter(Mandatory = $true)][string]$Root,
    [Parameter(Mandatory = $true)][int]$Port
  )

  $pythonPath = Join-Path $Root "venv\Scripts\python.exe"
  $serverPath = Join-Path $Root "server.py"

  if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "MAMGA Python not found: $pythonPath"
  }
  if (-not (Test-Path -LiteralPath $serverPath)) {
    throw "MAMGA server not found: $serverPath"
  }

  $env:MAMGA_PORT = [string]$Port
  Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @($serverPath) `
    -WorkingDirectory $Root `
    -WindowStyle Hidden | Out-Null
}

if (-not $ProjectRoot) {
  $ProjectRoot = Get-DefaultProjectRoot
}

$mamgaUrl = "http://127.0.0.1:$MamgaPort/health"

Write-Host "ECC vibe start"
Write-Host "Project: $ProjectRoot"
Write-Host "MAMGA: $mamgaUrl"
Write-Host ""

if (Test-MamgaHealth $mamgaUrl) {
  Write-Host "[OK] MAMGA memory already running"
} elseif ($SkipMamgaStart) {
  Write-Host "[WARN] MAMGA memory is not running and startup was skipped"
} else {
  Write-Host "[INFO] Starting MAMGA memory service"
  try {
    Start-Mamga -Root $MamgaRoot -Port $MamgaPort
  } catch {
    Write-Host ("[ERROR] {0}" -f $_.Exception.Message)
  }

  $deadline = (Get-Date).AddSeconds($StartupTimeoutSec)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500
    if (Test-MamgaHealth $mamgaUrl) {
      Write-Host "[OK] MAMGA memory is healthy"
      break
    }
  }

  if (-not (Test-MamgaHealth $mamgaUrl)) {
    Write-Host "[WARN] MAMGA memory did not become healthy before timeout"
    Write-Host "      recovery: $MamgaRoot\venv\Scripts\python.exe $MamgaRoot\server.py"
  }
}

Write-Host ""
$harnessPath = Join-Path $PSScriptRoot "vibe-harness.ps1"
if (Test-Path -LiteralPath $harnessPath) {
  if ($ForCline) {
    & $harnessPath run -ProjectRoot $ProjectRoot -ForCline
  } else {
    & $harnessPath run -ProjectRoot $ProjectRoot
  }
} else {
  Write-Host "[WARN] vibe-harness.ps1 not found next to vibestart.ps1"
}
