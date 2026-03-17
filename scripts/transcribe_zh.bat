@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "VENV_PYTHON=%SCRIPT_DIR%..\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
  echo Could not find virtual environment Python at "%VENV_PYTHON%".
  echo Create the environment first before using this script.
  pause
  exit /b 1
)

if "%~1"=="" (
  echo Drag a video file onto this script.
  pause
  exit /b 1
)
"%VENV_PYTHON%" -m window_transcribe_shortcut.main "%~1" --preset en2zh
if errorlevel 1 pause
