@echo off
REM ============================================================
REM  Instalador del RAG de calidad (rag-qa-playwright)
REM  Doble clic en este archivo, o desde la terminal: instalar.bat
REM
REM  Que hace:
REM   1. Crea un entorno de Python en %USERPROFILE%\.venvs\rag-qa-playwright
REM      (fuera de OneDrive, para que no sincronice miles de archivos).
REM   2. Instala las librerias (chromadb, sentence-transformers, mcp, pytest).
REM   3. Indexa la base de conocimiento, configura Copilot y ejecuta las pruebas.
REM
REM  Se puede ejecutar de nuevo cuantas veces quieras: no rompe nada.
REM ============================================================
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "VENV=%USERPROFILE%\.venvs\rag-qa-playwright"
set "PY=%VENV%\Scripts\python.exe"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "PYTHONUTF8=1"

echo.
echo ==== Instalador del RAG de calidad: rag-qa-playwright ====
echo.

if exist "%PY%" goto venv_listo
echo [1/3] Creando entorno de Python en %VENV%
python -m venv "%VENV%"
if errorlevel 1 goto error_python
goto instalar

:venv_listo
echo [1/3] Entorno de Python ya existe: %VENV%

:instalar
echo.
echo [2/3] Instalando librerias. La primera vez tarda varios minutos...
"%PY%" -m pip install --upgrade pip --quiet --disable-pip-version-check
"%PY%" -m pip install -e ".[test]" --disable-pip-version-check
if errorlevel 1 goto error_pip

echo.
echo [3/3] Indexando, configurando Copilot y ejecutando pruebas...
"%PY%" -m rag_qa.instalar
if errorlevel 1 goto error_final

echo.
pause
exit /b 0

:error_python
echo.
echo ERROR: no se pudo crear el entorno de Python.
echo Verifica que Python 3.10 o superior este instalado con: python --version
goto fin_error

:error_pip
echo.
echo ERROR: no se pudieron instalar las librerias. Revisa tu conexion a internet
echo y copia el mensaje de error de arriba para revisarlo.
goto fin_error

:error_final
echo.
echo La instalacion termino con errores. Copia el mensaje de arriba para revisarlo.

:fin_error
echo.
pause
exit /b 1
