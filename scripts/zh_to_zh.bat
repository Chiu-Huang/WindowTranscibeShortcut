@echo off
python -m window_transcribe_shortcut.main "%~1" --preset zh2zh
if errorlevel 1 pause
