@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_all_servers.ps1"
if errorlevel 1 pause
endlocal
