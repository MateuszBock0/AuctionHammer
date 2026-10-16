@echo off
setlocal
cd /d "%~dp0"
echo ================================================
echo           AUCTIONHAMMER - START

echo ================================================
where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 tools\bootstrap.py %*
) else (
  python tools\bootstrap.py %*
)
if errorlevel 1 (
  echo.
  echo Nie udalo sie uruchomic AuctionHammer.
  echo Sprawdz blad powyzej. Jesli wystapil pypi.org, to problem sieci lub DNS.
  pause
)
endlocal
