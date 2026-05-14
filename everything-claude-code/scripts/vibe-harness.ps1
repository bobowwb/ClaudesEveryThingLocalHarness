param(
  [string]$CommandOrProjectRoot = "run",
  [string]$ProjectRoot = "",
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

if ($CommandOrProjectRoot -in @("run", "check", "preflight")) {
  if (-not $ProjectRoot) {
    $ProjectRoot = Get-DefaultProjectRoot
  }
} else {
  $ProjectRoot = $CommandOrProjectRoot
}

function Test-CommandAvailable {
  param([Parameter(Mandatory = $true)][string]$Name)
  return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Add-Check {
  param(
    [Parameter(Mandatory = $true)][string]$Name,
    [Parameter(Mandatory = $true)][bool]$Ok,
    [Parameter(Mandatory = $true)][string]$Detail,
    [string]$Recovery = ""
  )

  [pscustomobject]@{
    Name = $Name
    Ok = $Ok
    Detail = $Detail
    Recovery = $Recovery
  }
}

$checks = @()
$mamgaUrl = "http://127.0.0.1:7788/health"

try {
  $mamga = Invoke-RestMethod -Uri $mamgaUrl -TimeoutSec 2
  $checks += Add-Check "MAMGA memory" ($mamga.status -eq "ok") "health=$($mamga.status) url=$mamgaUrl" "Run: .\vibestart.ps1"
} catch {
  $checks += Add-Check "MAMGA memory" $false "not reachable at $mamgaUrl" "Run: .\vibestart.ps1"
}

$browserHarness = Test-CommandAvailable "browser-harness"
$checks += Add-Check "browser-harness" $browserHarness $(if ($browserHarness) { "browser-harness is on PATH" } else { "browser-harness is not on PATH" }) "Use: C:\AI\browser-harness\SKILL.md or add browser-harness to PATH"

$agentBrowser = Test-Path -LiteralPath "C:\AI\agent-browser\CLINE_UI_TEST_GUIDE.md"
$checks += Add-Check "agent-browser" $agentBrowser $(if ($agentBrowser) { "C:\AI\agent-browser\CLINE_UI_TEST_GUIDE.md" } else { "missing Cline UI test guide" }) "Use browser-harness first; agent-browser is the Cline-oriented fallback"

$wiki = Test-Path -LiteralPath "C:\AI\obsidian-wiki\CLINE.md"
$checks += Add-Check "Obsidian wiki" $wiki $(if ($wiki) { "C:\AI\obsidian-wiki\CLINE.md" } else { "missing Cline wiki rule file" }) "Restore or point to the active wiki CLINE.md"

$plandb = (Test-Path -LiteralPath "C:\AI\plandb\plandb.bat") -or (Test-CommandAvailable "plandb")
$checks += Add-Check "PlanDB" $plandb $(if ($plandb) { "available as an optional task splitter" } else { "not available; optional for small tasks" }) "Prefer ECC planner/product-capability before development; use plandb only to split a complex approved plan. If a prompt says pladb, treat it as plandb."

$evolver = (Test-Path -LiteralPath "C:\AI\evolver\SKILL.md") -or (Test-CommandAvailable "evolver")
$checks += Add-Check "Evolver" $evolver $(if ($evolver) { "available, but keep review/manual mode" } else { "not available" }) "Run only after tests expose repeatable failures"

$codexConfig = Test-Path -LiteralPath (Join-Path $ProjectRoot ".codex\config.toml")
$checks += Add-Check "Codex project config" $codexConfig $(if ($codexConfig) { Join-Path $ProjectRoot ".codex\config.toml" } else { "missing .codex\config.toml" }) "Codex ignores project-local notify/profiles; move those to user config if needed"

Write-Host "ECC vibe harness preflight"
Write-Host "Project: $ProjectRoot"
Write-Host ""

foreach ($check in $checks) {
  $mark = if ($check.Ok) { "OK" } else { "WARN" }
  Write-Host ("[{0}] {1}: {2}" -f $mark, $check.Name, $check.Detail)
  if (-not $check.Ok -and $check.Recovery) {
    Write-Host ("      recovery: {0}" -f $check.Recovery)
  }
}

Write-Host ""
Write-Host "Shared harness policy for Cline/Codex:"
Write-Host "- Evidence priority: local tests/results > official docs > MAMGA memory > Obsidian wiki > other web/notes."
Write-Host "- Before coding: read AGENTS.md, run vibestart.ps1, and check MAMGA/Obsidian for project-specific memory."
Write-Host "- Browser work: prefer browser-harness; use agent-browser as the Cline command workflow fallback."
Write-Host "- Planning before development: prefer the ECC planner agent for implementation plans; use product-capability when product intent or cross-service constraints need a durable contract."
Write-Host "- PlanDB is optional and should be used only to split a complex approved plan into explicit steps."
Write-Host "- Evolver is review-only by default; apply evolution only when tests prove a repeated failure pattern."
Write-Host "- For Codex MCP warnings: keep fragile MCPs secondary; continue with built-in tools/skills when context7, memory, or playwright fail."
Write-Host "- For Cline thought/tool warnings: proceed, restate the work as a short checklist, then run only the next concrete step."

if ($ForCline) {
  Write-Host ""
  Write-Host "Paste into Cline session:"
  Write-Host "Follow AGENTS.md plus C:\AI\obsidian-wiki\CLINE.md. Use MAMGA at http://127.0.0.1:7788 for session memory, browser-harness/agent-browser for browser tasks, and trust tests before docs before memory/wiki. Before development, use the ECC planner agent for implementation plans or product-capability for constraint-heavy product work. If Cline shows a thought-process/tool warning, click Proceed Anyway and continue with one small concrete step; use plandb only to split an approved complex plan."
}
