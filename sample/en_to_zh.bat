@echo off
setlocal
if "%~1"=="" (
  echo Please drag a video file onto this script.
  pause
  exit /b 1
)
set "API_URL=http://127.0.0.1:8765/transcribe"
set "VIDEO_PATH=%~1"
set "PRESET=en2zh"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$payload = @{ video = [System.IO.Path]::GetFullPath($env:VIDEO_PATH); preset = $env:PRESET } | ConvertTo-Json;" ^
  "$response = Invoke-RestMethod -Uri $env:API_URL -Method Post -ContentType 'application/json' -Body $payload;" ^
  "Write-Host ('Done! Subtitle saved to: ' + $response.output)"
if errorlevel 1 (
  echo API request failed. Make sure the FastAPI server is running: ..\scripts\start_api_server.bat
  pause
)
