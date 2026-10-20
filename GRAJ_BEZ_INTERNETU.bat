@echo off
setlocal
cd /d "%~dp0"
rem Offline never checks GitHub. Works with both 0.9.43+ versioned and old EXE layouts.
if exist "%~dp0tools\portable_launcher.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1" -SkipUpdate
  if errorlevel 1 (
    echo [Blad] Nie mozna uruchomic zapisanej wersji offline.
    pause
    exit /b 1
  )
  exit /b 0
)
if exist "%~dp0AuctionHammer.exe" (
  start "" "%~dp0AuctionHammer.exe"
  exit /b 0
)
echo [Brak EXE] Przynajmniej raz pobierz wersje Windows z GitHub.
pause
exit /b 2
