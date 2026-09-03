@echo off
setlocal
cd /d "%~dp0"

echo Iniciando Controle de Certificados Digitais...
echo.

if not exist "venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual "venv" nao encontrado nesta pasta.
    pause
    exit /b 1
)

echo Este computador ficara acessivel para os outros micros da rede interna em:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do (
    echo   http://%%a:8501 ^| substitua %%a se houver mais de um IP e use o correto
)
echo   http://localhost:8501  ^(neste computador^)
echo.
echo Se outros PCs nao conseguirem acessar, libere a porta 8501 no Firewall do Windows.
echo.

"venv\Scripts\python.exe" run.py

pause
