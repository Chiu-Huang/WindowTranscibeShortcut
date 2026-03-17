@echo off
setlocal
if "%~1"=="" (
  echo Please drag a video file onto this script.
  pause
  exit /b 1
)
python -m window_transcribe_shortcut "%~1" --preset en2zh
if errorlevel 1 pause
