@echo off
setlocal
cd /d "%~dp0"

if not defined CARTOON_STUDIO_PORT set "CARTOON_STUDIO_PORT=8765"

if not exist ".venv\Scripts\python.exe" (
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo Python 3.11 or newer is required. Install Python 3.11 and try again.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
python -m pip install --require-hashes -r requirements.lock
if errorlevel 1 (
    echo Locked dependency installation failed. Check your internet connection and try again.
    pause
    exit /b 1
)

if not "%CARTOON_STUDIO_NO_BROWSER%"=="1" (
    start "" /min cmd /c "timeout /t 3 /nobreak ^>nul ^& start http://127.0.0.1:%CARTOON_STUDIO_PORT%"
)
python -m uvicorn app.main:app --host 127.0.0.1 --port %CARTOON_STUDIO_PORT%
pause
