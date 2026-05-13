# VWH Start - starts MCP server + browser dashboard
param([switch]$Verbose)
$ROOT=Split-Path $PSScriptRoot
$SRV=Join-Path $ROOT "scripts/mcp-server.js"
Write-Host ""
Write-Host "Starting VibeWiredHarness MCP server..." -ForegroundColor Cyan
try{$null=Invoke-WebRequest http://127.0.0.1:7788/health -TimeoutSec 2 -UseBasicParsing -EA Stop;Write-Host "  [OK] MAMGA :7788 running" -ForegroundColor Green}catch{Write-Host "  [--] MAMGA :7788 not detected - agents run without memory persistence" -ForegroundColor Yellow}
$n=(Get-ChildItem (Join-Path $ROOT "agents") -Filter "*.md" -EA SilentlyContinue).Count
Write-Host "  Wiring $n agents on MCP :3100..." -ForegroundColor Yellow
Start-Process -FilePath node -ArgumentList $SRV -NoNewWindow
Start-Sleep -Milliseconds 500
Write-Host ""
Write-Host "  MCP server started!" -ForegroundColor Green
Write-Host "  Dashboard:  http://localhost:3100" -ForegroundColor Cyan
Write-Host "  Health:     http://localhost:3100/ping" -ForegroundColor DarkGray
Write-Host "  Agents:     http://localhost:3100/tools/list" -ForegroundColor DarkGray
Write-Host ""
