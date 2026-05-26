@echo off
REM TalkCraft Coach v4.0 - Quick start script
cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist notu\Scripts\activate.bat (
    call notu\Scripts\activate.bat
)

REM Install the package in development mode
pip install -e talkcraft_coach >nul 2>&1

REM Run the coach server
python talkcraft_coach\main.py %*
