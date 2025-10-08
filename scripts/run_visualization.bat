@echo off
cd /d "%~dp0\.."

echo Visualizing Claude VLM classification results...
echo.

call venv\Scripts\activate.bat

echo Installing matplotlib if needed...
python3 -m pip install matplotlib

echo.
echo Creating annotated video and frames...
python3 src\visualize_classifications.py

echo.
echo Done! Check the following outputs:
echo   - embryo_classifications_annotated.mp4 (video with classifications)
echo   - 2_classified_png/ (individual annotated frames)
echo   - classification_summary.png (summary plot)
echo.
pause
