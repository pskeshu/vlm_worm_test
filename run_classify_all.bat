@echo off
echo Classifying ALL frames with Claude VLM...
echo.
echo This will analyze ALL 400 frames (not just sampled).
echo Estimated cost: ~$3.60
echo.
echo Make sure you have set ANTHROPIC_API_KEY environment variable!
echo Example: set ANTHROPIC_API_KEY=sk-ant-...
echo.
pause

call venv\Scripts\activate.bat

echo.
echo Running classification on all frames...
echo Results will be saved to embryo_classifications_all.json
echo You can interrupt and resume at any time (progress is saved after each frame).
echo.
python3 classify_all_frames.py

echo.
echo Done! Results saved to embryo_classifications_all.json
echo.
echo To visualize the results, run:
echo   python3 visualize_classifications.py --classifications embryo_classifications_all.json --output-video embryo_all_classifications.mp4
echo.
pause
