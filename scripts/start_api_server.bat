@echo off
setlocal
uv run window-transcribe-shortcut-api --warmup
if errorlevel 1 pause
