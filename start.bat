@echo off
setlocal enabledelayedexpansion

:: Omitir restricciones de ejecución para esta sesión
powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force"

:: 0. Iniciar Splash Screen (Loading Window) en paralelo
start /min powershell -WindowStyle Hidden -ExecutionPolicy Bypass -File "loading.ps1"

:: 1. Comprobar requisitos básicos (Python y Node)
where python >nul 2>nul
if %errorlevel% neq 0 (
    taskkill /f /fi "windowtitle eq Cargando Automate..." >nul 2>&1
    powershell -Command "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Python no esta instalado en este sistema. Por favor, instalalo para continuar.', 'Error de Requisitos', 'OK', 'Error')"
    exit /b 1
)
where npm >nul 2>nul
if %errorlevel% neq 0 (
    taskkill /f /fi "windowtitle eq Cargando Automate..." >nul 2>&1
    powershell -Command "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Node.js (npm) no esta instalado. Por favor, instalalo para continuar.', 'Error de Requisitos', 'OK', 'Error')"
    exit /b 1
)

if not exist "logs" mkdir logs

:: 2. Iniciar Backend (FastAPI con uvicorn) - ventana visible con /k para ver errores
echo [+] Iniciando Backend...
start "Automate Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn app:app --reload --port 8000"
timeout /t 3 /nobreak > nul

:: 3. Iniciar Frontend - ventana visible con /k para ver errores
echo [+] Iniciando Frontend...
start "Automate Frontend" cmd /k "cd frontend && npm run dev"

:: 4. Esperar y abrir la web
timeout /t 5 /nobreak > nul

:: 5. Cerrar Splash Screen
powershell -Command "Get-Process | Where-Object { $_.MainWindowTitle -eq 'Cargando Automate...' } | Stop-Process -Force" >nul 2>&1

:: Abrir la web automáticamente
start http://localhost:4321

exit /b 0
