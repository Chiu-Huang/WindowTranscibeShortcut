@echo off
setlocal
if "%~1"=="" (
  echo Please drag a video file onto this script.
  pause
  exit /b 1
)
uv run window-transcribe-shortcut "%~1" --preset ja2zh
if errorlevel 1 pause
