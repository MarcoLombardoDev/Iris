@echo off
echo ========================================
echo    EMAIL SENDER - BUILD
echo ========================================
echo.

py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10 or newer and try again.
    pause
    exit /b 1
)

echo Installing the development dependencies...
py -m pip install -r requirements-dev.txt

echo.
echo Running the tests...
py -m pytest tests -q
if errorlevel 1 (
    echo.
    echo ERROR: the tests did not pass. Build aborted.
    pause
    exit /b 1
)

echo.
echo Building the executable...
py build.py

echo.
echo Press any key to close...
pause >nul
