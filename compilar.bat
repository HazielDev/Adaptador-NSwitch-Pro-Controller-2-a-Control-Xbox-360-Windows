@echo off
REM Reconstruye dist\Adaptador Pro Controller 2.exe tras editar el codigo.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m venv .venv || python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" -m pip install pyinstaller --quiet
".venv\Scripts\python.exe" -m PyInstaller adaptador.spec --noconfirm --workpath "%TEMP%\adaptador-build" --distpath dist
if errorlevel 1 (
    echo.
    echo FALLO la compilacion.
    pause
    exit /b 1
)

echo.
echo Listo: dist\Adaptador Pro Controller 2.exe
echo Si el adaptador estaba abierto, cierralo antes de compilar.
pause
