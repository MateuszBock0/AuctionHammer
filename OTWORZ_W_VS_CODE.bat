@echo off
cd /d "%~dp0"
where code >nul 2>&1
if not errorlevel 1 (
 code .
) else (
 echo VS Code: File - Open Folder - wybierz AuctionHammer.
 pause
)
