@echo off
:: VibeWiredHarness root-level claude-l shim
:: Delegates to everything-claude-code\scripts\claude-l.cmd
setlocal
set "_ECC=%~dp0everything-claude-code\scripts"
if exist "%_ECC%\claude-l.cmd" (
  call "%_ECC%\claude-l.cmd" %*
) else (
  echo [ERROR] claude-l.cmd not found at %_ECC%
  echo Run .\install.ps1 first.
  exit /b 1
)
