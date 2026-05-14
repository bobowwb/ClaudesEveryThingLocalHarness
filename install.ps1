# VibeWiredHarness — one-line setup
param(
  [switch]$SkipNpm,
  [switch]$SkipEcc,
  [switch]$SkipPath,
  [switch]$SkipStart,
  [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$ROOT = $PSScriptRoot
$ECC  = Join-Path $ROOT "everything-claude-code"

function Write-Step { param([string]$msg) Write-Host $msg -ForegroundColor Cyan }
function Write-Ok   { param([string]$msg) Write-Host "[OK]   $msg" -ForegroundColor Green }
function Write-Warn { param([string]$msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err  { param([string]$msg) Write-Host "[ERR]  $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "=== VibeWiredHarness Setup ===" -ForegroundColor Cyan
Write-Host "Root:  $ROOT"
Write-Host "ECC:   $ECC"
Write-Host ""

# ── 1. Node.js ──────────────────────────────────────────────────────────────
$nv = node --version 2>$null
if (-not $nv) {
  Write-Err "Node.js not found — install from https://nodejs.org (LTS)"
  exit 1
}
Write-Ok "Node $nv"

# ── 2. npm install ───────────────────────────────────────────────────────────
if (-not $SkipNpm) {
  Write-Step "Installing root dependencies..."
  if (-not $DryRun) { Push-Location $ROOT; npm install --silent; Pop-Location }

  if (Test-Path (Join-Path $ECC "package.json")) {
    Write-Step "Installing ECC dependencies..."
    if (-not $DryRun) { Push-Location $ECC; npm install --silent; Pop-Location }
  }
  Write-Ok "npm install done"
}

# ── 3. .env from example ────────────────────────────────────────────────────
$envFile    = Join-Path $ROOT ".env"
$envExample = Join-Path $ROOT ".env.example"
if (-not (Test-Path $envFile)) {
  if (Test-Path $envExample) {
    if (-not $DryRun) { Copy-Item $envExample $envFile }
    Write-Warn ".env created from .env.example — edit it and set ANTHROPIC_API_KEY or HYPERSPACE_PROXY_KEY"
  } else {
    Write-Warn "No .env or .env.example found — create .env with ANTHROPIC_API_KEY=<key>"
  }
} else {
  Write-Ok ".env exists"
}

# ── 4. Add scripts to user PATH (no admin required) ─────────────────────────
if (-not $SkipPath) {
  $pathsToAdd = @(
    $ROOT,                              # claude-l.cmd at root
    (Join-Path $ECC "scripts")          # original claude-l.cmd
  )

  $userPath = [Environment]::GetEnvironmentVariable("PATH", "User") ?? ""
  $added    = @()

  foreach ($p in $pathsToAdd) {
    if ($userPath -split ";" | Where-Object { $_.TrimEnd("\") -eq $p.TrimEnd("\") }) {
      # already in PATH
    } else {
      $userPath = "$p;$userPath"
      $added   += $p
    }
  }

  if ($added.Count -gt 0) {
    if (-not $DryRun) {
      [Environment]::SetEnvironmentVariable("PATH", $userPath, "User")
      $env:PATH = ($added -join ";") + ";$env:PATH"
    }
    Write-Ok "Added to user PATH (restart terminal to take full effect):"
    $added | ForEach-Object { Write-Host "  $_" }
  } else {
    Write-Ok "PATH already configured"
  }
}

# ── 5. Install ECC into ~/.claude/ ──────────────────────────────────────────
if (-not $SkipEcc) {
  $eccInstall = Join-Path $ECC "scripts\install-apply.js"
  if (Test-Path $eccInstall) {
    Write-Step "Installing ECC into ~/.claude/ (604 files, agents, skills, hooks)..."
    if (-not $DryRun) {
      Push-Location $ECC
      $eccArgs = @("scripts/install-apply.js", "--profile", "full", "--target", "claude")
      $result  = node @eccArgs 2>&1
      Pop-Location
      if ($LASTEXITCODE -ne 0) {
        Write-Warn "ECC install exited $LASTEXITCODE — check output above"
        $result | Write-Host
      } else {
        Write-Ok "ECC installed into ~/.claude/"
      }
    } else {
      Write-Ok "[dry-run] would run: node scripts/install-apply.js --profile full --target claude"
    }
  } else {
    Write-Warn "ECC install-apply.js not found at $eccInstall — skipping ~/.claude/ setup"
  }
}

# ── 6. vibestart preflight ───────────────────────────────────────────────────
if (-not $SkipStart) {
  $vs = Join-Path $ECC "scripts\vibestart.ps1"
  if (Test-Path $vs) {
    Write-Host ""
    Write-Step "Running vibestart preflight..."
    if (-not $DryRun) { & $vs } else { Write-Ok "[dry-run] would run vibestart.ps1" }
  }
}

# ── Summary ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "  Launch Claude:  claude-l           (from this dir or ECC subdir)"
Write-Host "  Start services: .\everything-claude-code\scripts\vibestart.ps1"
Write-Host "  Stop services:  .\everything-claude-code\scripts\vibestop.ps1"
Write-Host "  Update:         git pull            (updates all — root + ECC together)"
Write-Host ""
Write-Host "If claude-l is not found yet, restart your terminal (PATH was just updated)."
