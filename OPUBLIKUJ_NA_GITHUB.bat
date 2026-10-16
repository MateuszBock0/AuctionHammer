@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\publish_to_github.ps1"
if errorlevel 1 (
 echo.
 echo Publikacja nie powiodla sie. Przeczytaj komunikat powyzej.
 pause
 exit /b 1
)
echo.
echo Pliki opublikowane. Sprawdz zakladke Actions w przegladarce.
pause
endlocal
