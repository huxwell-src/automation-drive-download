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

:: 2. Backend: Entorno Virtual e Instalación de dependencias de Python
if not exist "logs" mkdir logs

if not exist "backend\.venv" (
    python -m venv backend\.venv
)

if exist "backend\requirements.txt" (
    backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt --quiet
)

:: 3. Frontend: Instalación de dependencias de Node.js
if exist "frontend\package.json" (
    cd frontend
    if not exist "node_modules" (
        echo [!] Instalando dependencias de Node...
        npm install --quiet > ..\logs\npm_install.log 2>&1
    ) else (
        echo [!] Actualizando dependencias de Node...
        npm install --quiet > ..\logs\npm_install.log 2>&1
    )
    cd ..
)

:: 4. Iniciar Servidores en Segundo Plano (Minimizados)
echo [+] Iniciando Backend...
start /min "Automate Backend" cmd /c "cd backend && .venv\Scripts\python.exe app.py > ..\logs\backend.log 2>&1"
timeout /t 3 /nobreak > nul

echo [+] Iniciando Frontend...
start /min "Automate Frontend" cmd /c "cd frontend && npm run dev > ..\logs\frontend.log 2>&1"

:: 5. Esperar y abrir la web
timeout /t 5 /nobreak > nul

:: 6. Logs y Finalización de Splash Screen
powershell -Command "Get-Process | Where-Object { $_.MainWindowTitle -eq 'Cargando Automate...' } | Stop-Process -Force" >nul 2>&1

:: Abrir la web automáticamente
start http://localhost:4321

exit /b 0
