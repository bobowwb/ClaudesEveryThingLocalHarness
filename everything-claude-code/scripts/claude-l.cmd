@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: claude-l: launch Claude Code against the local Hyperspace LiteLLM proxy via
:: claude-code-router (ccr), which translates Anthropic Messages API <-> OpenAI
:: chat completions. The router reads its config from
:: %USERPROFILE%\.claude-code-router\config.json.

where claude >nul 2>nul
if errorlevel 1 (
  echo Claude CLI not found on PATH. Install Claude Code or add claude.exe to PATH.
  exit /b 127
)

where ccr >nul 2>nul
if errorlevel 1 (
  echo claude-code-router ^(ccr^) not found on PATH.
  echo Install it with:  npm i -g @musistudio/claude-code-router
  exit /b 127
)

set "CLAUDE_L_DEFAULT_MODEL=anthropic--claude-4.7-opus"
if not defined CLAUDE_CODE_NO_FLICKER set "CLAUDE_CODE_NO_FLICKER=1"
if not defined CLAUDE_CODE_DISABLE_TERMINAL_TITLE set "CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1"

:: ccr owns the upstream auth (configured in ~/.claude-code-router/config.json),
:: so we deliberately clear Anthropic-side credentials to avoid double-auth.
set "ANTHROPIC_API_KEY="
set "ANTHROPIC_AUTH_TOKEN="
set "ANTHROPIC_BASE_URL="
set "ANTHROPIC_CUSTOM_HEADERS="

if not defined ANTHROPIC_MODEL (
  if /i not "%CLAUDE_L_PROMPT_MODEL%"=="1" (
    set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"
  )
)

if not defined ANTHROPIC_MODEL (
  echo.
  echo Select Claude model:
  echo   1^) anthropic--claude-4.7-opus ^(default^)
  echo   2^) anthropic--claude-4.6-sonnet
  echo   3^) anthropic--claude-4.5-sonnet
  echo   4^) anthropic--claude-4-sonnet
  echo   5^) anthropic--claude-4.6-opus
  echo   6^) anthropic--claude-4.5-opus
  echo   7^) anthropic--claude-4.5-haiku
  echo   8^) custom
  set /p "CLAUDE_L_MODEL_CHOICE=Model [1]: "

  if "!CLAUDE_L_MODEL_CHOICE!"=="2" set "ANTHROPIC_MODEL=anthropic--claude-4.6-sonnet"
  if "!CLAUDE_L_MODEL_CHOICE!"=="3" set "ANTHROPIC_MODEL=anthropic--claude-4.5-sonnet"
  if "!CLAUDE_L_MODEL_CHOICE!"=="4" set "ANTHROPIC_MODEL=anthropic--claude-4-sonnet"
  if "!CLAUDE_L_MODEL_CHOICE!"=="5" set "ANTHROPIC_MODEL=anthropic--claude-4.6-opus"
  if "!CLAUDE_L_MODEL_CHOICE!"=="6" set "ANTHROPIC_MODEL=anthropic--claude-4.5-opus"
  if "!CLAUDE_L_MODEL_CHOICE!"=="7" set "ANTHROPIC_MODEL=anthropic--claude-4.5-haiku"
  if "!CLAUDE_L_MODEL_CHOICE!"=="8" set /p "ANTHROPIC_MODEL=Custom model: "
  if not defined ANTHROPIC_MODEL set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"
)

set "CLAUDE_MODEL=%ANTHROPIC_MODEL%"

echo [claude-l] Routing through ccr -^> http://localhost:6655/litellm/v1
echo [claude-l] Model: %ANTHROPIC_MODEL%

call ccr code %*
set "CLAUDE_L_EXIT=%ERRORLEVEL%"
exit /b %CLAUDE_L_EXIT%