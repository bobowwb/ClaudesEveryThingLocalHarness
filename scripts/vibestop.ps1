# VibeWiredHarness - Stop Script
# Stops Layer 1 ONLY (MCP :3100). Does NOT stop MAMGA or Layer 2 services.
param([switch]$Force)
$MCP_PORT = 3100
Write-Host ""
Write-Host "Stopping VibeWiredHarness (Layer 1 - MCP :$MCP_PORT)..." -ForegroundColor Cyan
Write-Host "NOTE: MAMGA :7788 and Layer 2 services are NOT stopped here." -ForegroundColor DarkGray
$conns = netstat -ano 2>$null | Select-String ":$MCP_PORT "
if ($conns) {
    $conns | ForEach-Object {
        $p = $_.ToString().Trim() -split "\\s+"
        $pidv = $p[-1]
        if ($pidv -match "\\d+$" -and $pidv -ne "0") {
            Write-Host "  Killing PID $pidv" -ForegroundColor Yellow
            if ($Force) { taskkill /PID $pidv /F 2>$null } else { taskkill /PID $pidv 2>$null }
        }
    }
} else { Write-Host "  No process on port $MCP_PORT" -ForegroundColor Gray }
Write-Host "Stopped." -ForegroundColor Green
Write-Host ""
