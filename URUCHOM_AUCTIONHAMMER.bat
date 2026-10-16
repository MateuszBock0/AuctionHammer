@echo off
setlocal
cd /d "%~dp0"

rem Allow bootstrap from source-only folder: updater downloads portable EXE on first run.
if exist "%~dp0tools\portable_launcher.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1"
  if not errorlevel 1 goto :done
  echo [Aktualizator] Could not update or start the portable version.
)

if exist "%~dp0AuctionHammer.exe" (
  start "" "%~dp0AuctionHammer.exe"
  goto :done
)

echo [Missing EXE] An Internet connection is required to download the first Windows release.
echo https://github.com/MateuszBock0/AuctionHammer/releases/latest
pause

:done
endlocal
