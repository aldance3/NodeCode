@echo off
cd /d "%~dp0"
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Done! Run the agent with:
echo   run.bat
echo   or: python main.py
pause
