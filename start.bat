@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\containercraft-cli.exe" (
    ".venv\Scripts\containercraft-cli.exe" %*
) else (
    uv run containercraft-cli %*
)
