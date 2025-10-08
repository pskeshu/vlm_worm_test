@echo off
echo Creating interactive HTML viewer for embryo classifications...
echo.

call venv\Scripts\activate.bat

echo Generating viewer...
echo This will create a standalone HTML file with all images embedded.
echo The file will be large (~100-200 MB) but completely self-contained.
echo.
python3 create_interactive_viewer.py

echo.
echo Done! Open embryo_viewer.html in your web browser.
echo.
echo Features:
echo   - Navigate with arrow buttons or keyboard arrows
echo   - Play/pause timelapse
echo   - View classifications, confidence, and reasoning
echo   - Jump to any frame with slider
echo.
pause
