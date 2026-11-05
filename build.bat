@echo off
REM Construit dist\PetiteSoif\PetiteSoif.exe sur ton PC (environ 2 minutes).
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate.bat || goto :err
python -m pip install --upgrade pip >nul
python -m pip install -r requirements-build.txt || goto :err
python -m PyInstaller --noconfirm --clean petite_soif.spec || goto :err
echo.
echo OK : dist\PetiteSoif\PetiteSoif.exe
pause
exit /b 0
:err
echo.
echo Echec du build, voir les messages ci-dessus.
pause
exit /b 1
