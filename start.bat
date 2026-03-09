@echo off
setlocal enabledelayedexpansion

:: 0. Comprobar requisitos básicos (Python y Node)
where python >nul 2>nul
if %errorlevel% neq 0 (
    powershell -Command "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Python no esta instalado en este sistema. Por favor, instalalo para continuar.', 'Error de Requisitos', 'OK', 'Error')"
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    powershell -Command "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Node.js (npm) no esta instalado. Por favor, instalalo para continuar.', 'Error de Requisitos', 'OK', 'Error')"
    exit /b 1
)

:: Mostrar mensaje de inicio (solo si no se corre oculto, pero útil para saber que algo pasa)
echo [+] Configurando y lanzando Automate...

:: 1. Backend: Entorno Virtual e Instalación de dependencias de Python
if not exist "backend\.venv" (
    python -m venv backend\.venv
)

if exist "backend\requirements.txt" (
    backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt --quiet
)

:: 2. Frontend: Instalación de dependencias de Node.js
if exist "frontend\package.json" (
    if not exist "frontend\node_modules" (
        cd frontend && npm install --quiet && cd ..
    )
)

:: 3. Iniciar Servidores en Segundo Plano (Minimizados)
start /min "Automate Backend" cmd /c "cd backend && .venv\Scripts\python.exe app.py"
timeout /t 3 /nobreak > nul

start /min "Automate Frontend" cmd /c "cd frontend && npm run dev"

:: 4. Esperar y abrir la web
timeout /t 5 /nobreak > nul
start http://localhost:4321

:: Notificación de éxito (opcional, el navegador ya es la señal)
powershell -Command "[Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Automate se ha iniciado correctamente. La web se abrira en tu navegador.', 'Automate - Listo', 'OK', 'Information')"

exit /b 0
