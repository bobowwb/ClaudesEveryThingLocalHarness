# VWH Install
param([switch]$SkipNpm)
$ROOT=$PSScriptRoot
Write-Host "=== VibeWiredHarness Install ==="
$nv=node --version 2>$null;if(-not $nv){exit 1}
Write-Host "Node $nv"
if(-not $SkipNpm){Set-Location $ROOT;npm install}
$ag=Join-Path $ROOT "agents";$ags=Get-ChildItem $ag -Filter "*.md";$names=$ags|%{$_.BaseName}
Write-Host "Wiring $($ags.Count) agents:"
$names|%{Write-Host "  - $_"}
$cd=Join-Path $ROOT ".codex";if(-not(Test-Path $cd)){New-Item -IT Directory $cd|Out-Null}
Set-Content (Join-Path $cd "agents-manifest.json") (@{generated=(Get-Date -F "s");count=$ags.Count;agents=$names}|ConvertTo-Json -D 3) -E UTF8
Write-Host "Manifest ok"
$cfg=Join-Path $ROOT ".codex/config.toml";if(-not(Test-Path $cfg)){Write-Host "MISSING config.toml";exit 1}
$ep=Join-Path $ROOT ".env";if(-not(Test-Path $ep)){$ex=Join-Path $ROOT ".env.example";if(Test-Path $ex){Copy-Item $ex $ep;Write-Host "Created .env - set ANTHROPIC_API_KEY"}}
Write-Host "=== Done $($ags.Count) agents ==="
Write-Host "Start: .\scripts\vibestart.ps1"
Write-Host "Dashboard: http://localhost:3100"
