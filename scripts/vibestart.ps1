# VibeWiredHarness - Start Script
# NOTE: Start MAMGA :7788 BEFORE running this
param([switch]$Verbose)
$MCP_PORT=3100
$ROOT=Split-Path $PSScriptRoot
Write-Host ""
Write-Host "Starting VibeWiredHarness (Layer 1 - MCP :$MCP_PORT)..." -ForegroundColor Cyan
try{$null=Invoke-WebRequest "http://127.0.0.1:7788/health" -TimeoutSec 2 -UseBasicParsing -EA Stop;Write-Host "  [OK] MAMGA :7788 running" -ForegroundColor Green}catch{Write-Host "  [WARN] MAMGA :7788 not reachable" -ForegroundColor Yellow}
$agents=Get-ChildItem (Join-Path $ROOT "agents") -Filter "*.md"
Write-Host "  Wiring $($agents.Count) agents into MCP :$MCP_PORT..." -ForegroundColor Yellow
if($Verbose){$agents|ForEach-Object{Write-Host "    - $($_.BaseName)" -ForegroundColor DarkGray}}
Start-Process -FilePath "node" -ArgumentList (Join-Path $ROOT "scripts\mcp-server.js") -NoNewWindow
Write-Host "$($agents.Count) agents on MCP :$MCP_PORT - started!" -ForegroundColor Green
Write-Host "Status: .\scripts\vibestatus.ps1"
Write-Host "Stop:   .\scripts\vibestop.ps1"
