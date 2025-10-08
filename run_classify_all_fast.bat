@echo off
echo Classifying ALL frames CONCURRENTLY with Claude VLM (FAST MODE)...
echo.
echo This will process multiple frames in parallel for much faster classification!
echo.
echo Settings:
echo   - Frames: ALL 400 frames
echo   - Concurrent requests: 5 (adjustable with --max-concurrent)
echo   - Estimated cost: ~$3.60
echo   - Estimated time: ~4 minutes (vs ~20 minutes sequential)
echo.
echo Make sure you have set ANTHROPIC_API_KEY environment variable!
echo Example: set ANTHROPIC_API_KEY=sk-ant-...
echo.
pause

call venv\Scripts\activate.bat

echo.
echo Running CONCURRENT classification on all frames...
echo Results will be saved to embryo_classifications_all.json
echo.
python3 classify_all_frames_concurrent.py --max-concurrent 5

echo.
echo Done! Results saved to embryo_classifications_all.json
echo.
echo To visualize the results, run:
echo   python3 visualize_classifications.py --classifications embryo_classifications_all.json
echo.
pause
