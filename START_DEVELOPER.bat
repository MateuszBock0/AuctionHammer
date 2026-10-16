@echo off
cd /d "%~dp0"
echo Tryb developerski wymaga Pythona i pygame-ce; zwykla gra korzysta z AuctionHammer.exe.
where py >nul 2>&1
if not errorlevel 1 (py -3 -m game.main) else (python -m game.main)
if errorlevel 1 pause
