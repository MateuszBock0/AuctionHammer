@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0AuctionHammer.exe" (
  echo [Brak EXE] To folder z kodem zrodlowym, a nie gotowa gra Windows.
  echo Pobierz AuctionHammer-Windows.zip z:
  echo https://github.com/MateuszBock0/AuctionHammer/releases/latest
  echo Wydanie zawiera AuctionHammer.exe i biblioteki - bez instalacji Pythona.
  pause
  exit /b 2
)

if exist "%~dp0tools\portable_launcher.ps1" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\portable_launcher.ps1"
  if not errorlevel 1 goto :done
  echo [Aktualizator] Blad sprawdzania aktualizacji. Uruchamiam lokalne EXE.
)
start "" "%~dp0AuctionHammer.exe"
:done
endlocal
