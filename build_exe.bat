@echo off
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "BOOTSTRAP_PY=py -3.11"
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "BOOTSTRAP_PY="%LocalAppData%\Programs\Python\Python311\python.exe""
if not exist ".venv\Scripts\python.exe" (
  %BOOTSTRAP_PY% -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pytest -q
if errorlevel 1 exit /b 1
".venv\Scripts\pyinstaller.exe" --noconfirm --clean RAWPilot.spec
if errorlevel 1 exit /b 1
echo.
echo Build complete: dist\RAWPilot.exe
endlocal
