@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem Local Claude launcher for Windows cmd.exe/PowerShell terminals.
rem All environment changes are scoped by setlocal and are reverted on exit.

set "__CLAUDE_L_OLD_CP="
for /f "tokens=2 delims=:" %%A in ('chcp 2^>nul') do set "__CLAUDE_L_OLD_CP=%%A"
set "__CLAUDE_L_OLD_CP=%__CLAUDE_L_OLD_CP: =%"
chcp 65001 >nul 2>nul

set "ANTHROPIC_BASE_URL=http://localhost:6655/anthropic"
set "CLAUDE_L_DEFAULT_MODEL=anthropic--claude-4.6-sonnet"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
set "LANG=C.UTF-8"
set "LC_ALL=C.UTF-8"
set "TERM=xterm-256color"
set "COLORTERM=truecolor"
set "FORCE_COLOR=1"
set "CLICOLOR_FORCE=1"
set "CLAUDE_CODE_NO_FLICKER=1"
set "CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1"

if defined ANTHROPIC_AUTH_TOKEN goto claude_l_have_auth_token
if not defined HYPERSPACE_PROXY_KEY goto claude_l_check_hyperspace_api_key
set "ANTHROPIC_AUTH_TOKEN=%HYPERSPACE_PROXY_KEY%"

:claude_l_check_hyperspace_api_key
if defined ANTHROPIC_AUTH_TOKEN goto claude_l_have_auth_token
if not defined HYPERSPACE_API_KEY goto claude_l_check_api_key
set "ANTHROPIC_AUTH_TOKEN=%HYPERSPACE_API_KEY%"

:claude_l_check_api_key
if defined ANTHROPIC_AUTH_TOKEN goto claude_l_have_auth_token
if not defined ANTHROPIC_API_KEY goto claude_l_prompt_auth_token
set "ANTHROPIC_AUTH_TOKEN=%ANTHROPIC_API_KEY%"

:claude_l_have_auth_token
if defined ANTHROPIC_API_KEY goto claude_l_auth_done
set "ANTHROPIC_API_KEY=%ANTHROPIC_AUTH_TOKEN%"
goto claude_l_auth_done

:claude_l_prompt_auth_token
set /p "ANTHROPIC_AUTH_TOKEN=Hyperspace proxy API key: "
set "ANTHROPIC_API_KEY=%ANTHROPIC_AUTH_TOKEN%"

:claude_l_auth_done
if defined ANTHROPIC_MODEL goto claude_l_model_done

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

if "%CLAUDE_L_MODEL_CHOICE%"=="2" set "ANTHROPIC_MODEL=anthropic--claude-4.5-sonnet"
if "%CLAUDE_L_MODEL_CHOICE%"=="3" set "ANTHROPIC_MODEL=anthropic--claude-4-sonnet"
if "%CLAUDE_L_MODEL_CHOICE%"=="4" set "ANTHROPIC_MODEL=anthropic--claude-4.6-opus"
if "%CLAUDE_L_MODEL_CHOICE%"=="5" set "ANTHROPIC_MODEL=anthropic--claude-4.5-opus"
if "%CLAUDE_L_MODEL_CHOICE%"=="6" set "ANTHROPIC_MODEL=anthropic--claude-4.5-haiku"
if "%CLAUDE_L_MODEL_CHOICE%"=="7" set /p "ANTHROPIC_MODEL=Custom model: "
if not defined ANTHROPIC_MODEL set "ANTHROPIC_MODEL=%CLAUDE_L_DEFAULT_MODEL%"

:claude_l_model_done
set "ANTHROPIC_CUSTOM_HEADERS=Authorization: Bearer %ANTHROPIC_AUTH_TOKEN%"

claude --model "%ANTHROPIC_MODEL%" %*
set "__CLAUDE_L_EXIT_CODE=%ERRORLEVEL%"

if defined __CLAUDE_L_OLD_CP chcp %__CLAUDE_L_OLD_CP% >nul 2>nul
exit /b %__CLAUDE_L_EXIT_CODE%
