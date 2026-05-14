@echo off
setlocal EnableExtensions EnableDelayedExpansion

where claude >nul 2>nul
if errorlevel 1 (
  echo Claude CLI not found on PATH. Install Claude Code or add claude.exe to PATH.
  exit /b 127
)

if not defined ANTHROPIC_BASE_URL set "ANTHROPIC_BASE_URL=http://localhost:6655/anthropic"
set "CLAUDE_L_DEFAULT_MODEL=anthropic--claude-4.6-sonnet"
if not defined CLAUDE_CODE_NO_FLICKER set "CLAUDE_CODE_NO_FLICKER=1"
if not defined CLAUDE_CODE_DISABLE_TERMINAL_TITLE set "CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1"

if not defined ANTHROPIC_AUTH_TOKEN (
  if defined HYPERSPACE_PROXY_KEY set "ANTHROPIC_AUTH_TOKEN=%HYPERSPACE_PROXY_KEY%"
)

if not defined ANTHROPIC_API_KEY (
  if defined ANTHROPIC_AUTH_TOKEN set "ANTHROPIC_API_KEY=%ANTHROPIC_AUTH_TOKEN%"
)

if not defined ANTHROPIC_AUTH_TOKEN (
  if defined ANTHROPIC_API_KEY set "ANTHROPIC_AUTH_TOKEN=%ANTHROPIC_API_KEY%"
)

if not defined ANTHROPIC_AUTH_TOKEN (
  set /p "ANTHROPIC_AUTH_TOKEN=Hyperspace proxy API key: "
  set "ANTHROPIC_API_KEY=!ANTHROPIC_AUTH_TOKEN!"
)

if not defined ANTHROPIC_MODEL (
  if /i not "%CLAUDE_L_PROMPT_MODEL%"=="1" (
    set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"
  )
)

if not defined ANTHROPIC_MODEL (
  echo.
  echo Select Claude model:
  echo   1^) anthropic--claude-4.6-sonnet ^(default^)
  echo   2^) anthropic--claude-4.5-sonnet
  echo   3^) anthropic--claude-4-sonnet
  echo   4^) anthropic--claude-4.6-opus
  echo   5^) anthropic--claude-4.5-opus
  echo   6^) anthropic--claude-4.5-haiku
  echo   7^) custom
  set /p "CLAUDE_L_MODEL_CHOICE=Model [1]: "

  if "!CLAUDE_L_MODEL_CHOICE!"=="2" set "ANTHROPIC_MODEL=anthropic--claude-4.5-sonnet"
  if "!CLAUDE_L_MODEL_CHOICE!"=="3" set "ANTHROPIC_MODEL=anthropic--claude-4-sonnet"
  if "!CLAUDE_L_MODEL_CHOICE!"=="4" set "ANTHROPIC_MODEL=anthropic--claude-4.6-opus"
  if "!CLAUDE_L_MODEL_CHOICE!"=="5" set "ANTHROPIC_MODEL=anthropic--claude-4.5-opus"
  if "!CLAUDE_L_MODEL_CHOICE!"=="6" set "ANTHROPIC_MODEL=anthropic--claude-4.5-haiku"
  if "!CLAUDE_L_MODEL_CHOICE!"=="7" set /p "ANTHROPIC_MODEL=Custom model: "
  if not defined ANTHROPIC_MODEL set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"
)

set "ANTHROPIC_CUSTOM_HEADERS=Authorization: Bearer %ANTHROPIC_AUTH_TOKEN%"

claude --model "%ANTHROPIC_MODEL%" %*
set "CLAUDE_L_EXIT=%ERRORLEVEL%"
exit /b %CLAUDE_L_EXIT%
