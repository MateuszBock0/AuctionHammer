@echo off
setlocal
cd /d "%~dp0"

rem AuctionHammer 0.9.43: verified side-by-side updater. Existing user saves stay untouched.
if exist "%~dp0tools\portable_launcher.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1"
  if errorlevel 1 (
    echo.
    echo [AuctionHammer] Launcher returned an error. The old version has NOT been overwritten.
    echo [Pomoc] https://github.com/MateuszBock0/AuctionHammer/releases/latest
    pause
    exit /b 1
  )
  exit /b 0
)

rem Legacy or source-only fallback for old folders without a PowerShell launcher.
if exist "%~dp0AuctionHammer.exe" (
  start "" "%~dp0AuctionHammer.exe"
  exit /b 0
)
echo [Brak EXE] Rozpakuj najnowszy Windows ZIP lub umiesc ten BAT obok katalogu tools.
echo https://github.com/MateuszBock0/AuctionHammer/releases/latest
pause
exit /b 2
