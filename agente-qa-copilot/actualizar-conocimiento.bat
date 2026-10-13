@echo off
REM ============================================================
REM  Copia la base de conocimiento oficial del RAG a este agente.
REM  Ejecutalo cada vez que se agregue o cambie un documento en
REM  ..\rag-qa-playwright\knowledge-base
REM ============================================================
setlocal
cd /d "%~dp0"
set "ORIGEN=..\rag-qa-playwright\knowledge-base"
set "DESTINO=.github\qa-conocimiento"

if not exist "%ORIGEN%" (
  echo No se encontro la carpeta %ORIGEN%
  echo Este archivo debe estar dentro de qaAutomatizador, al lado de rag-qa-playwright.
  pause
  exit /b 1
)

xcopy "%ORIGEN%" "%DESTINO%" /E /I /Y /Q
if errorlevel 1 (
  echo ERROR al copiar los documentos.
  pause
  exit /b 1
)
echo.
echo Conocimiento actualizado en %DESTINO%
pause
