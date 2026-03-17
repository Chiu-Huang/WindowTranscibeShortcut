@echo off
python -m window_transcribe_shortcut.main "%~1" --preset en2zh
if errorlevel 1 pause
