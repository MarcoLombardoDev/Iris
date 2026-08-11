@echo off
REM Start Email Sender from source
echo Starting Email Sender...

py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10 or newer and try again.
    pause
    exit /b 1
)

py main.py
if errorlevel 1 (
    echo.
    echo The application exited with an error.
    echo If dependencies are missing, run install_dependencies.bat
    pause
)
