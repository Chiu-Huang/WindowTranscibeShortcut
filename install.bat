@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"
echo [WindowTranscibeShortcut] Installing dependencies...

after_uv_check:
where uv >nul 2>nul
if errorlevel 1 (
  echo.
  echo [ERROR] uv is not installed or not in PATH.
  echo Install uv first: https://docs.astral.sh/uv/getting-started/installation/
  echo Then run this script again.
  pause
  exit /b 1
)

echo [1/1] Running: uv sync
uv sync
if errorlevel 1 (
  echo.
  echo [ERROR] uv sync failed.
  pause
  exit /b 1
)

echo.
echo [OK] Dependencies installed successfully.
echo You can now run start.vbs to launch the app.
pause
exit /b 0
