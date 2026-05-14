# VWH Start - starts MCP observer + browser dashboard
param([switch]$Verbose)

$ROOT = Split-Path $PSScriptRoot
$SRV = Join-Path $ROOT "scripts/mcp-server.js"
$MCP_PORT = if ($env:MCP_PORT) { [int]$env:MCP_PORT } else { 3100 }
$BASE_URL = "http://127.0.0.1:$MCP_PORT"

Write-Host ""
Write-Host "Starting VibeWiredHarness MCP observer on :$MCP_PORT..." -ForegroundColor Cyan
try {
    $null = Invoke-WebRequest http://127.0.0.1:7788/health -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "  [OK] MAMGA :7788 running" -ForegroundColor Green
} catch {
    Write-Host "  [--] MAMGA :7788 not detected - agents run without memory persistence" -ForegroundColor Yellow
}

$n = (Get-ChildItem (Join-Path $ROOT "agents") -Filter "*.md" -ErrorAction SilentlyContinue).Count
Write-Host "  Wiring $n agents on MCP :$MCP_PORT..." -ForegroundColor Yellow

function Test-VwhHealth {
    try {
        $response = Invoke-WebRequest "$BASE_URL/ping" -TimeoutSec 1 -UseBasicParsing -ErrorAction Stop
        $body = $response.Content | ConvertFrom-Json
        return ($body.status -eq "ok" -and $body.layer -eq "1-mcp")
    } catch {
        return $false
    }
}

if (Test-VwhHealth) {
    Write-Host ""
    Write-Host "  MCP observer is already running and passed /ping." -ForegroundColor Green
    Write-Host "  Dashboard:  $BASE_URL" -ForegroundColor Cyan
    Write-Host "  Health:     $BASE_URL/ping" -ForegroundColor DarkGray
    Write-Host "  Agents:     $BASE_URL/tools/list" -ForegroundColor DarkGray
    Write-Host ""
    exit 0
}

$proc = Start-Process -FilePath node -ArgumentList $SRV -WindowStyle Hidden -PassThru
$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 250
    if ($proc.HasExited) { break }
    if (Test-VwhHealth) {
        $healthy = $true
        break
    }
}

Write-Host ""
if ($healthy) {
    Write-Host "  MCP observer started and passed /ping." -ForegroundColor Green
    Write-Host "  Dashboard:  $BASE_URL" -ForegroundColor Cyan
    Write-Host "  Health:     $BASE_URL/ping" -ForegroundColor DarkGray
    Write-Host "  Agents:     $BASE_URL/tools/list" -ForegroundColor DarkGray
} elseif ($proc.HasExited) {
    Write-Host "  [FAIL] MCP observer process exited before /ping responded. Exit code: $($proc.ExitCode)" -ForegroundColor Red
    Write-Host "  Run: node --check scripts/mcp-server.js" -ForegroundColor DarkGray
} else {
    Write-Host "  [WARN] MCP observer process started as PID $($proc.Id), but /ping did not respond on $BASE_URL." -ForegroundColor Yellow
    Write-Host "  Dashboard URL withheld until health check passes." -ForegroundColor DarkGray
}
Write-Host ""
