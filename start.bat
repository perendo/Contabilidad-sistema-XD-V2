@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual de Python...
    py -3.12 -m venv venv
    if errorlevel 1 goto :error
)

call "venv\Scripts\activate.bat"
if errorlevel 1 goto :error

echo Iniciando la aplicacion...
python start.py
set "EXIT_CODE=%ERRORLEVEL%"
pause
exit /b %EXIT_CODE%

:error
echo ERROR: No se pudo preparar o iniciar la aplicacion.
pause
exit /b 1
