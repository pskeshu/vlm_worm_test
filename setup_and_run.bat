@echo off
echo Creating virtual environment...
python3 -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing requirements...
python3 -m pip install numpy tifffile opencv-python tqdm pandas

echo.
echo Setup complete! Running script...
echo.
python3 make_max_projection_video.py

echo.
echo Done! Video saved as embryo1_max_projection.mp4
pause
