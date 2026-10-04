@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
if errorlevel 1 (
  echo.
  echo Installation failed. Please copy the error above when reporting an issue.
  pause
  exit /b 1
)
echo.
echo Installation completed successfully.
pause
