@echo off
cd /d "%~dp0\.."

echo Running embryo classification with Claude...
echo.
echo Make sure you have set ANTHROPIC_API_KEY environment variable!
echo Example: set ANTHROPIC_API_KEY=sk-ant-...
echo.
pause

call venv\Scripts\activate.bat

echo.
echo Installing anthropic package if needed...
python3 -m pip install anthropic pillow

echo.
echo Running classification (sampling every 10 minutes)...
echo This will analyze frames and save results to embryo_classifications.json
echo.
python3 src\classify_embryo_stages.py --frames-dir 1_png --interval 10

echo.
echo Done! Results saved to embryo_classifications.json
pause
