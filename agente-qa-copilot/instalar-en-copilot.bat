@echo off
REM ============================================================
REM  Instala los agentes QA en tu Copilot (perfil de usuario).
REM  Despues de esto, QA Revisor y QA Nuevo Proyecto aparecen en
REM  CUALQUIER proyecto que abras en VS Code, no solo en esta carpeta.
REM
REM  No necesita permisos de administrador: solo copia archivos
REM  a %USERPROFILE%\.copilot
REM  Se puede ejecutar de nuevo para actualizar los agentes.
REM ============================================================
setlocal
cd /d "%~dp0"
set "DESTINO=%USERPROFILE%\.copilot"

echo.
echo Instalando agentes QA en %DESTINO% ...
echo.

xcopy ".github\agents" "%DESTINO%\agents" /E /I /Y /Q
if errorlevel 1 goto error
xcopy ".github\qa-conocimiento" "%DESTINO%\qa-conocimiento" /E /I /Y /Q
if errorlevel 1 goto error

echo.
echo ============================================================
echo  Listo. Agentes instalados:
echo    - QA Revisor
echo    - QA Nuevo Proyecto
echo.
echo  1. Cierra y vuelve a abrir VS Code.
echo  2. Abre cualquier proyecto y el chat de Copilot: Ctrl+Alt+I
echo  3. Elige el agente en el selector donde dice Agent.
echo ============================================================
echo.
pause
exit /b 0

:error
echo.
echo ERROR al copiar los archivos. Copia el mensaje de arriba para revisarlo.
pause
exit /b 1
