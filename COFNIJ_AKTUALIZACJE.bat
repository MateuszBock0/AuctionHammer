@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0tools\portable_launcher.ps1" (
  echo [Rollback] Brak aktualizatora. Przywroc pelny ZIP AuctionHammer.
  pause
  exit /b 2
)
echo [Rollback] Przywracam poprzednia zweryfikowana wersje AuctionHammer...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1" -Rollback
if errorlevel 1 (
  echo [Rollback] Nie mozna przywrocic poprzedniej wersji.
  pause
  exit /b 1
)
exit /b 0
