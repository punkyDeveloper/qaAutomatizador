@echo off
REM ============================================================
REM  Instalador UNICO de qaAutomatizador.
REM  Doble clic en este archivo (o desde la terminal: instalar.bat).
REM
REM  Que hace, en orden:
REM   [1/3] Actualiza el conocimiento de los agentes de Copilot
REM         (copia rag-qa-playwright\knowledge-base a
REM          agente-qa-copilot\.github\qa-conocimiento).
REM   [2/3] Instala los agentes QA Revisor y QA Nuevo Proyecto en tu
REM         perfil de Copilot (%USERPROFILE%\.copilot). No necesita Python.
REM   [3/3] Instala el RAG: entorno de Python, librerias, indexa los
REM         documentos, configura Copilot y ejecuta las pruebas.
REM         Necesita Python 3.10 o superior. Si no esta, los agentes
REM         quedan instalados igual y se explica como terminar.
REM
REM  Seguridad: no pide administrador y no borra carpetas tuyas.
REM  Si una carpeta de origen o destino es un enlace o una union
REM  (apunta a otra carpeta), se detiene sin copiar nada.
REM  Las librerias de Python se instalan desde requirements.lock con
REM  sus huellas (hashes): si un paquete fue alterado, pip lo rechaza.
REM  Antes de reemplazar los agentes en tu Copilot guarda una copia en
REM  %USERPROFILE%\.copilot\respaldo-AAAAMMDD-HHMMSS.
REM  Se puede ejecutar cuantas veces quieras: no rompe nada.
REM
REM  Codigos de salida: 0 = todo bien, 1 = error,
REM                     2 = agentes instalados pero el RAG no (falta Python).
REM  Opcional: instalar.bat /sinpausa  -> no espera una tecla al final
REM            (sirve para probarlo de forma automatica).
REM ============================================================
setlocal EnableExtensions

REM Herramientas de Windows con ruta completa: asi no se ejecuta por error
REM un robocopy.cmd, where.exe o powershell.exe que este en esta carpeta.
set "SYS=%SystemRoot%\System32"
set "ROBOCOPY=%SYS%\robocopy.exe"
set "WHERE=%SYS%\where.exe"
set "POWERSHELL=%SYS%\WindowsPowerShell\v1.0\powershell.exe"
set "CHCP=%SYS%\chcp.com"
REM Opciones comunes de robocopy. /XJ: no entra en uniones ni enlaces.
REM Sin ">nul": si robocopy falla, su mensaje de error queda en pantalla.
set "OPC_COPIA=/XJ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP"

REM Guardamos el codigo de pagina de la consola para dejarlo igual al salir.
set "CP_ANTERIOR="
for /f "tokens=2 delims=:." %%C in ('"%CHCP%"') do set "CP_ANTERIOR=%%C"
if defined CP_ANTERIOR set "CP_ANTERIOR=%CP_ANTERIOR: =%"
"%CHCP%" 65001 >nul

REM Trabajamos siempre desde la carpeta donde esta este archivo.
cd /d "%~dp0"

set "SINPAUSA=0"
if /i "%~1"=="/sinpausa" set "SINPAUSA=1"

echo.
echo ==== Instalador de qaAutomatizador ====
echo.

REM Tu carpeta de usuario debe existir: ahi se instalan los agentes y el RAG.
if "%USERPROFILE%"=="" goto error_perfil
if not exist "%USERPROFILE%\" goto error_perfil

REM Rutas absolutas, para no depender de la carpeta actual.
set "RAIZ=%~dp0"
set "RAG=%RAIZ%rag-qa-playwright"
set "AGENTE=%RAIZ%agente-qa-copilot"
set "COPILOT=%USERPROFILE%\.copilot"
set "VENV=%USERPROFILE%\.venvs\rag-qa-playwright"
set "PY=%VENV%\Scripts\python.exe"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "PYTHONUTF8=1"

REM ------------------------------------------------------------
REM [1/3] Actualizar el conocimiento de los agentes
REM ------------------------------------------------------------
echo [1/3] Actualizando el conocimiento de los agentes...
if not exist "%RAG%\knowledge-base\" goto error_falta_kb
if not exist "%AGENTE%\.github\" goto error_falta_agente
REM /MIR borra en el destino lo que no esta en el origen. Si el destino
REM fuera un enlace o una union, borraria archivos de otra carpeta tuya.
REM Por eso antes se revisa que ni el origen ni el destino lo sean.
call :revisar_sin_enlace "%RAG%\knowledge-base" || goto error_enlace
call :revisar_sin_enlace "%AGENTE%" || goto error_enlace
call :revisar_sin_enlace "%AGENTE%\.github" || goto error_enlace
call :revisar_sin_enlace "%AGENTE%\.github\qa-conocimiento" || goto error_enlace
REM Si knowledge-base no tiene ningun documento .md, /MIR vaciaria las copias.
dir /b /s "%RAG%\knowledge-base\*.md" >nul 2>&1 || goto error_kb_vacia
REM robocopy /MIR deja la copia igual al original (quita documentos viejos).
REM robocopy devuelve 0 a 7 cuando todo salio bien y 8 o mas cuando hubo error.
"%ROBOCOPY%" "%RAG%\knowledge-base" "%AGENTE%\.github\qa-conocimiento" /MIR %OPC_COPIA%
if errorlevel 8 goto error_copia
echo       Listo: conocimiento copiado a agente-qa-copilot\.github\qa-conocimiento
echo.

REM ------------------------------------------------------------
REM [2/3] Instalar los agentes en el perfil de Copilot
REM ------------------------------------------------------------
echo [2/3] Instalando los agentes en tu Copilot...
if not exist "%AGENTE%\.github\agents\" goto error_falta_agente

REM Antes de respaldar y copiar, se revisa que las carpetas de Copilot
REM no sean enlaces ni uniones.
call :revisar_sin_enlace "%AGENTE%\.github\agents" || goto error_enlace
call :revisar_sin_enlace "%COPILOT%" || goto error_enlace
call :revisar_sin_enlace "%COPILOT%\agents" || goto error_enlace
call :revisar_sin_enlace "%COPILOT%\qa-conocimiento" || goto error_enlace

REM Respaldo: si ya habia agentes o conocimiento instalados, se copian
REM a una carpeta con fecha y hora antes de reemplazarlos.
call :hacer_respaldo
if errorlevel 1 goto error_copia

REM Los agentes se copian sin borrar otros agentes que tengas en Copilot.
"%ROBOCOPY%" "%AGENTE%\.github\agents" "%COPILOT%\agents" /E %OPC_COPIA%
if errorlevel 8 goto error_copia
REM El conocimiento queda igual al del proyecto (quita documentos viejos).
"%ROBOCOPY%" "%AGENTE%\.github\qa-conocimiento" "%COPILOT%\qa-conocimiento" /MIR %OPC_COPIA%
if errorlevel 8 goto error_copia
echo       Listo: QA Revisor y QA Nuevo Proyecto instalados en "%COPILOT%"
echo.

REM ------------------------------------------------------------
REM [3/3] Instalar el RAG (necesita Python 3.10 o superior)
REM ------------------------------------------------------------
echo [3/3] Instalando el RAG (rag-qa-playwright)...
if not exist "%RAG%\pyproject.toml" goto error_falta_rag

REM Si el entorno ya existe y funciona, se reutiliza.
REM Si existe pero esta danado o es de un Python viejo, se recrea limpio
REM (--clear borra solo esa carpeta, que es exclusiva del RAG).
set "VENV_CLEAR="
if not exist "%VENV%\" goto buscar_python
if not exist "%PY%" goto venv_danado
"%PY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto venv_listo
:venv_danado
echo       El entorno "%VENV%" no funciona: se va a crear de nuevo.
set "VENV_CLEAR=--clear"

:buscar_python
REM Buscamos Python 3.10+: primero el lanzador oficial "py -3" (si existe),
REM luego "python". En los dos casos se comprueba la version antes de seguir.
set "PYBASE="
set "PYVIEJO=0"
"%WHERE%" py >nul 2>&1
if errorlevel 1 goto probar_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYBASE=py -3"
if defined PYBASE goto crear_venv
py -3 -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYVIEJO=1"

:probar_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 set "PYBASE=python"
if defined PYBASE goto crear_venv
python -c "import sys" >nul 2>&1
if not errorlevel 1 set "PYVIEJO=1"
goto sin_python

:crear_venv
echo       Creando entorno de Python en "%VENV%"
%PYBASE% -m venv %VENV_CLEAR% "%VENV%"
if errorlevel 1 goto error_venv
goto instalar_librerias

:venv_listo
echo       Entorno de Python ya existe: "%VENV%"

:instalar_librerias
echo       Instalando librerias. La primera vez tarda varios minutos...
REM pip y setuptools al dia. setuptools 84.1 o superior corrige
REM GHSA-xmj3-9gf7-h52w (escritura fuera de carpeta al instalar en Windows).
"%PY%" -m pip install --upgrade pip "setuptools>=84.1" --quiet --disable-pip-version-check
if errorlevel 1 goto error_pip

REM requirements.lock fija la version exacta y la huella (hash) de cada
REM libreria. Se genero para Windows y Python 3.13. Con otra version de
REM Python se usa la instalacion normal (sin huellas) y se avisa.
if not exist "%RAG%\requirements.lock" goto pip_sin_lock
"%PY%" -c "import sys; sys.exit(0 if sys.version_info[:2] == (3, 13) else 1)" >nul 2>&1
if errorlevel 1 goto pip_sin_lock

REM --require-hashes: si un paquete descargado no coincide con su huella,
REM pip lo rechaza (protege de paquetes alterados en PyPI).
"%PY%" -m pip install --require-hashes -r "%RAG%\requirements.lock" --quiet --disable-pip-version-check
if errorlevel 1 goto error_pip
REM El proyecto se instala sin volver a buscar dependencias (--no-deps) y con
REM el setuptools ya verificado del entorno (--no-build-isolation).
"%PY%" -m pip install --no-deps --no-build-isolation -e "%RAG%[test]" --quiet --disable-pip-version-check
if errorlevel 1 goto error_pip
goto librerias_listas

:pip_sin_lock
echo       AVISO: tu Python no es 3.13 o falta requirements.lock; se instalan
echo       las librerias sin verificar huellas (hashes).
REM --upgrade-strategy only-if-needed: si una libreria ya instalada es mas
REM antigua que la version minima segura de pyproject.toml, se actualiza.
"%PY%" -m pip install -e "%RAG%[test]" --upgrade-strategy only-if-needed --disable-pip-version-check
if errorlevel 1 goto error_pip

:librerias_listas

echo       Indexando, configurando Copilot y ejecutando pruebas...
"%PY%" -m rag_qa.instalar
if errorlevel 1 goto error_rag

echo.
echo ============================================================
echo  Instalacion completa: agentes de Copilot y RAG listos.
echo  Cierra y vuelve a abrir VS Code para ver los agentes.
echo ============================================================
call :pausa
exit /b 0

REM ------------------------------------------------------------
REM Sin Python: los agentes ya quedaron instalados (funcionan sin RAG).
REM ------------------------------------------------------------
:sin_python
echo.
echo ============================================================
echo  Los agentes de Copilot quedaron INSTALADOS y funcionan sin RAG
echo  (leen el conocimiento directamente de los documentos).
echo.
if "%PYVIEJO%"=="1" echo  El RAG NO se instalo: tu Python es anterior a 3.10 y el RAG necesita 3.10 o superior.
if "%PYVIEJO%"=="0" echo  El RAG NO se instalo: no se encontro Python en este computador.
echo  Para instalarlo:
echo   1. Instala Python 3.10+ desde https://www.python.org/downloads/
echo      (marca "Add python.exe to PATH"; no necesita administrador
echo       si eliges "Install for me only").
echo   2. Cierra esta ventana y vuelve a hacer doble clic en instalar.bat.
echo ============================================================
call :pausa
exit /b 2

REM ------------------------------------------------------------
REM Mensajes de error
REM ------------------------------------------------------------
:error_perfil
echo.
echo ERROR: no se encontro tu carpeta de usuario (variable USERPROFILE).
echo Cierra la sesion de Windows, vuelve a entrar y ejecuta de nuevo instalar.bat.
goto fin_error

:error_falta_kb
echo.
echo ERROR: no se encontro la carpeta "%RAG%\knowledge-base".
echo Este archivo debe estar en la carpeta qaAutomatizador, junto a rag-qa-playwright.
goto fin_error

:error_kb_vacia
echo.
echo ERROR: la carpeta "%RAG%\knowledge-base" no tiene ningun documento .md.
echo No se copia nada para no vaciar el conocimiento ya instalado.
goto fin_error

:error_enlace
echo.
echo ERROR: la carpeta "%CARPETA_ENLACE%" es un enlace o una union
echo (apunta a otra carpeta). No se copia nada para no borrar archivos ajenos.
echo Reemplazala por una carpeta normal y vuelve a ejecutar instalar.bat.
goto fin_error

:error_falta_agente
echo.
echo ERROR: no se encontro la carpeta "%AGENTE%\.github" o su subcarpeta agents.
echo Este archivo debe estar en la carpeta qaAutomatizador, junto a agente-qa-copilot.
goto fin_error

:error_falta_rag
echo.
echo ERROR: no se encontro "%RAG%\pyproject.toml".
echo Los agentes de Copilot si quedaron instalados.
goto fin_error

:error_copia
echo.
echo ERROR al copiar los archivos. Copia el mensaje de arriba para revisarlo.
goto fin_error

:error_venv
echo.
echo ERROR: no se pudo crear el entorno de Python en "%VENV%".
echo Los agentes de Copilot si quedaron instalados.
echo Verifica Python con: python --version
goto fin_error

:error_pip
echo.
echo ERROR: no se pudieron instalar las librerias del RAG. Revisa tu conexion
echo a internet y copia el mensaje de error de arriba para revisarlo.
echo Los agentes de Copilot si quedaron instalados.
goto fin_error

:error_rag
echo.
echo El RAG termino con errores. Copia el mensaje de arriba para revisarlo.
echo Los agentes de Copilot si quedaron instalados.

:fin_error
call :pausa
exit /b 1

REM ------------------------------------------------------------
REM Copia los agentes y el conocimiento ya instalados a
REM %COPILOT%\respaldo-AAAAMMDD-HHMMSS. Si no hay nada instalado, no hace nada.
REM Devuelve 1 si la copia falla.
REM ------------------------------------------------------------
:hacer_respaldo
if not exist "%COPILOT%\agents\" if not exist "%COPILOT%\qa-conocimiento\" exit /b 0
set "FECHA="
REM Solo dos comillas (las de la ruta): con mas comillas, cmd quita la
REM primera y la ultima y el comando de PowerShell se rompe.
for /f "delims=" %%F in ('"%POWERSHELL%" -NoProfile -Command Get-Date -Format yyyyMMdd-HHmmss 2^>nul') do set "FECHA=%%F"
if not defined FECHA set "FECHA=sin-fecha-%RANDOM%"
set "RESPALDO=%COPILOT%\respaldo-%FECHA%"
if not exist "%COPILOT%\agents\" goto respaldo_conocimiento
"%ROBOCOPY%" "%COPILOT%\agents" "%RESPALDO%\agents" /E %OPC_COPIA%
if errorlevel 8 exit /b 1
:respaldo_conocimiento
if not exist "%COPILOT%\qa-conocimiento\" goto respaldo_listo
"%ROBOCOPY%" "%COPILOT%\qa-conocimiento" "%RESPALDO%\qa-conocimiento" /E %OPC_COPIA%
if errorlevel 8 exit /b 1
:respaldo_listo
echo       Respaldo de lo instalado antes: "%RESPALDO%"
call :limpiar_respaldos
exit /b 0

REM ------------------------------------------------------------
REM Conserva solo los 3 respaldos mas recientes en %COPILOT%.
REM Solo toca carpetas con el nombre exacto respaldo-AAAAMMDD-HHMMSS,
REM nunca la que se acaba de crear y nunca enlaces ni uniones.
REM "dir /o-n" los ordena del mas nuevo al mas viejo, "findstr" deja solo
REM los nombres exactos y "skip=3" salta los 3 mas nuevos. El borrado lo
REM hace "rd", que no entra en uniones. Si algo falla, se sigue igual.
REM ------------------------------------------------------------
:limpiar_respaldos
set "PATRON_RESPALDO=respaldo-[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]"
for /f "skip=3 delims=" %%R in ('dir /b /ad /o-n "%COPILOT%\respaldo-*" 2^>nul ^| "%SYS%\findstr.exe" /r /x "%PATRON_RESPALDO%"') do call :borrar_respaldo "%%R"
exit /b 0

:borrar_respaldo
if /i "%COPILOT%\%~1"=="%RESPALDO%" exit /b 0
call :revisar_sin_enlace "%COPILOT%\%~1" || exit /b 0
rd /s /q "%COPILOT%\%~1" 2>nul
if not exist "%COPILOT%\%~1\" echo       Respaldo viejo borrado: "%~1"
exit /b 0

REM ------------------------------------------------------------
REM Revisa que la carpeta %1 NO sea un enlace simbolico ni una union.
REM %~a1 da sus atributos; la letra "l" indica un enlace o una union.
REM Si la carpeta aun no existe, esta bien (robocopy la crea normal).
REM Devuelve 1 (y guarda la ruta en CARPETA_ENLACE) si es un enlace.
REM ------------------------------------------------------------
:revisar_sin_enlace
if not exist "%~1" exit /b 0
set "ATR=%~a1"
if not defined ATR exit /b 0
if "%ATR:l=%"=="%ATR%" exit /b 0
set "CARPETA_ENLACE=%~1"
exit /b 1

REM Espera una tecla, salvo que se haya pedido /sinpausa, y deja la
REM consola con el codigo de pagina que tenia antes. Todas las salidas
REM del instalador pasan por aqui.
:pausa
echo.
if "%SINPAUSA%"=="0" pause
if defined CP_ANTERIOR "%CHCP%" %CP_ANTERIOR% >nul
exit /b 0
