@echo off
setlocal
title MEDUSA 0.3.0
cd /d "%~dp0"
echo MEDUSA 0.3.0
echo Cartella: %~dp0
if exist ".venv\Scripts\python.exe" goto run
where py >nul 2>&1
if errorlevel 1 goto usepython
py -3 -m venv .venv
if errorlevel 1 goto error
goto install
:usepython
where python >nul 2>&1
if errorlevel 1 goto nopython
python -m venv .venv
if errorlevel 1 goto error
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
:run
".venv\Scripts\python.exe" -c "import PySide6, psutil" >nul 2>&1
if errorlevel 1 goto install
".venv\Scripts\python.exe" main.py
if errorlevel 1 goto error
exit /b 0
:nopython
echo Installa Python 3.10 o successivo a 64 bit da python.org e riprova.
pause
exit /b 1
:error
echo.
echo Avvio non riuscito. Leggi il messaggio sopra e invialo per assistenza.
pause
exit /b 1
