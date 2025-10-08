@echo off
cd /d "%~dp0\.."

echo Starting multithreaded HTTP server for embryo viewer...
echo.
python3 src\serve_viewer_multithreaded.py
