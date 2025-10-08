@echo off
echo Starting HTTP server for embryo viewer...
echo.
echo The viewer will be available at:
echo   http://localhost:8000/embryo_viewer_light.html
echo.
echo Press Ctrl+C to stop the server
echo.
python3 -m http.server 8000
