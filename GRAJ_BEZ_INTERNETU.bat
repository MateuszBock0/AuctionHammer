@echo off
setlocal
cd /d "%~dp0"
if not exist "AuctionHammer.exe" (
 echo AuctionHammer.exe was not found. Download the Windows release from GitHub.
 pause
 exit /b 1
)
start "" "%~dp0AuctionHammer.exe"
endlocal
