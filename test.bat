@echo off
echo Running the Email Sender test suite...

py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

py -m pytest tests -v
echo.
pause
