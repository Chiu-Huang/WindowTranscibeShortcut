@echo off
setlocal

cd /d "%~dp0"
set "TARGET=%~dp0start.vbs"
set "SHORTCUT=%USERPROFILE%\Desktop\WindowTranscibeShortcut.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$W=New-Object -ComObject WScript.Shell;" ^
  "$S=$W.CreateShortcut('%SHORTCUT%');" ^
  "$S.TargetPath='%TARGET%';" ^
  "$S.WorkingDirectory='%~dp0';" ^
  "$S.IconLocation='%SystemRoot%\\System32\\shell32.dll,220';" ^
  "$S.Save()"

if errorlevel 1 (
  echo [ERROR] Failed to create desktop shortcut.
  pause
  exit /b 1
)

echo [OK] Desktop shortcut created:
echo %SHORTCUT%
pause
exit /b 0
