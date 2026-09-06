@echo off
setlocal

set "BUNDLE_ROOT=%~dp0"
set "PROJECT_ROOT=%BUNDLE_ROOT%hazard-red-zone-system"
set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"

if not exist "%PROJECT_ROOT%\app.py" (
  echo ERROR: Hazard Command project folder was not found:
  echo   %PROJECT_ROOT%
  echo.
  echo Use the START_OFFLINE.cmd from the root of the extracted field bundle.
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo ERROR: Offline environment is not installed yet.
  echo.
  echo Run INSTALL_OFFLINE.ps1 first, then launch this file again.
  pause
  exit /b 1
)

cd /d "%PROJECT_ROOT%"

echo Hazard Command - validating offline field readiness...
"%PYTHON_EXE%" scripts\field_preflight.py --strict-road-cache
if errorlevel 1 (
  echo.
  echo ERROR: Strict field preflight failed. The app will not be launched as road-aware READY.
  echo Review the messages above, repair the bundle, then retry.
  pause
  exit /b 1
)

echo.
echo Starting Hazard Command in OFFLINE/LAN mode...
echo Keep this window open while using the app.
echo.
"%PYTHON_EXE%" scripts\run_offline.py

set "APP_EXIT=%ERRORLEVEL%"
if not "%APP_EXIT%"=="0" (
  echo.
  echo Hazard Command exited with code %APP_EXIT%.
  pause
)
exit /b %APP_EXIT%
