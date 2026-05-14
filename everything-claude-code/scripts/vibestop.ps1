param(
  [string]$MamgaRoot = "C:\AI\MAMGA",
  [int]$MamgaPort = 7788,
  [int]$GraceTimeoutSec = 5,
  [switch]$NoForce,
  [switch]$WhatIf
)

$ErrorActionPreference = "Continue"

function Test-MamgaHealth {
  param([Parameter(Mandatory = $true)][string]$Url)

  try {
    $response = Invoke-RestMethod -Uri $Url -TimeoutSec 2
    return $response.status -eq "ok"
  } catch {
    return $false
  }
}

function Get-MamgaProcesses {
  param([Parameter(Mandatory = $true)][string]$Root)

  $serverPath = Join-Path $Root "server.py"
  $escapedServerPath = [regex]::Escape($serverPath)

  Get-CimInstance Win32_Process |
    Where-Object {
      $_.CommandLine -and
      $_.CommandLine -match $escapedServerPath
    } |
    ForEach-Object {
      [pscustomobject]@{
        ProcessId = [int]$_.ProcessId
        Name = $_.Name
        CommandLine = $_.CommandLine
      }
    }
}

function Get-PortProcessIds {
  param([Parameter(Mandatory = $true)][int]$Port)

  if (-not (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue)) {
    return @()
  }

  try {
    return @(
      Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    )
  } catch {
    return @()
  }
}

function Stop-MamgaProcess {
  param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [Parameter(Mandatory = $true)][int]$TimeoutSec,
    [Parameter(Mandatory = $true)][bool]$AllowForce,
    [Parameter(Mandatory = $true)][bool]$DryRun
  )

  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if (-not $process) {
    Write-Host "[OK] MAMGA process $ProcessId is already stopped"
    return
  }

  if ($DryRun) {
    Write-Host "[WHATIF] Would stop MAMGA process $ProcessId"
    return
  }

  Write-Host "[INFO] Stopping MAMGA process $ProcessId"

  $closed = $false
  try {
    $closed = $process.CloseMainWindow()
  } catch {
    $closed = $false
  }

  if ($closed) {
    if ($process.WaitForExit($TimeoutSec * 1000)) {
      Write-Host "[OK] MAMGA process $ProcessId exited cleanly"
      return
    }
  }

  $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
  if (-not $process) {
    Write-Host "[OK] MAMGA process $ProcessId exited"
    return
  }

  if (-not $AllowForce) {
    Write-Host "[WARN] MAMGA process $ProcessId is still running; -NoForce prevented termination"
    return
  }

  Stop-Process -Id $ProcessId -Force
  Write-Host "[OK] MAMGA process $ProcessId terminated"
}

$mamgaUrl = "http://127.0.0.1:$MamgaPort/health"
$mamgaProcesses = @(Get-MamgaProcesses -Root $MamgaRoot)
$portProcessIds = @(Get-PortProcessIds -Port $MamgaPort)

Write-Host "ECC vibe stop"
Write-Host "MAMGA: $mamgaUrl"
Write-Host ""

if ($mamgaProcesses.Count -eq 0) {
  if (Test-MamgaHealth $mamgaUrl) {
    Write-Host "[WARN] MAMGA health is responding, but no process matched $MamgaRoot\server.py"
  } else {
    Write-Host "[OK] MAMGA memory is not running"
  }

  if ($portProcessIds.Count -gt 0) {
    Write-Host ("[INFO] Port {0} is owned by PID(s): {1}" -f $MamgaPort, ($portProcessIds -join ", "))
    Write-Host "       No action taken because they were not identified as MAMGA."
  }
  exit 0
}

foreach ($entry in $mamgaProcesses) {
  Stop-MamgaProcess -ProcessId $entry.ProcessId -TimeoutSec $GraceTimeoutSec -AllowForce:(-not $NoForce) -DryRun:$WhatIf
}

if ($WhatIf) {
  Write-Host "[WHATIF] No processes were stopped"
  exit 0
}

Start-Sleep -Milliseconds 500

if (Test-MamgaHealth $mamgaUrl) {
  Write-Host "[WARN] MAMGA health still responds after stop attempt"
} else {
  Write-Host "[OK] MAMGA memory stopped"
}
