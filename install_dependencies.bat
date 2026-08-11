@echo off
echo Installing the Email Sender dependencies...

py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10 or newer and try again.
    pause
    exit /b 1
)

py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR while installing the dependencies.
    pause
    exit /b 1
)

echo.
echo Installation complete.
echo Press any key to exit...
pause > nul
