@echo off
setlocal

REM Change the active directory to the one where this script is located.
cd /d "%~dp0"

REM Check if Python is installed and available in PATH.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found.
    echo Please install Python 3.10 or higher and make sure it's added to your system's PATH.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python detected.

REM Install dependencies from requirements.txt.
echo Installing dependencies...
pip install -r requirements.txt

REM Start the application.
echo Starting the application...
start "Flask App" cmd /c "python app.py"

echo Waiting for the server to start...
timeout /t 5 /nobreak > nul

echo Opening the application in your browser at http://127.0.0.1:5000
start http://127.0.0.1:5000

endlocal
pause
