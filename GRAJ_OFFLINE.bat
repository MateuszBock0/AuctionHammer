@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 tools\bootstrap.py --offline
) else (
  python tools\bootstrap.py --offline
)
if errorlevel 1 pause
endlocal
