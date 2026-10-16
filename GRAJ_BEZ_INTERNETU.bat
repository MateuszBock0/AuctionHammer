@echo off
setlocal
cd /d "%~dp0"
if not exist "AuctionHammer.exe" (
 echo Brak pliku AuctionHammer.exe. Pobierz gotowy pakiet z GitHub Releases.
 pause
 exit /b 1
)
start "" "%~dp0AuctionHammer.exe"
endlocal
