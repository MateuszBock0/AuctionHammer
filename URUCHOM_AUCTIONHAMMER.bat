@echo off
setlocal
cd /d "%~dp0"

rem Allow bootstrap from source-only folder: updater downloads portable EXE on first run.
if exist "%~dp0tools\portable_launcher.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1"
  if not errorlevel 1 goto :done
  echo [Aktualizator] Nie udalo sie pobrac lub uruchomic wersji portable.
)

if exist "%~dp0AuctionHammer.exe" (
  start "" "%~dp0AuctionHammer.exe"
  goto :done
)

echo [Brak EXE] Pierwsze uruchomienie wymaga dostepu do GitHub Releases.
echo https://github.com/MateuszBock0/AuctionHammer/releases/latest
pause

:done
endlocal
