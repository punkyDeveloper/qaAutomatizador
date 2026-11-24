r"""Prueba de punta a punta: ¿el RAG le sirve a un QA que automatiza con Playwright + POM?

Qué hace este script (en orden):
  1. revisar_codigo      -> código mal hecho (un anti-patrón por ejemplo) y código bien hecho.
  2. diagnosticar_error  -> errores REALES: copia la plantilla a una carpeta temporal,
                            ejecuta pruebas que fallan a propósito y le pasa el error al RAG.
  3. plantilla_proyecto  -> arma el proyecto con lo que devuelve y verifica que
                            `npx playwright test --list` lo reconoce.
  4. buscar_conocimiento -> preguntas de un QA en palabras sencillas.

Cada caso imprime ✅ o ❌ con una línea de explicación. Al final, el total.
Usa el modelo de embeddings real y una base vectorial temporal (no toca la del usuario).

Ejecutar (desde la carpeta rag-qa-playwright):
    set PYTHONIOENCODING=utf-8
    %USERPROFILE%\.venvs\rag-qa-playwright\Scripts\python.exe pruebas_automatizacion/probar_automatizacion.py
"""

from __future__ import annotations

import gc
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------- preparación
CARPETA_RAG = Path(__file__).resolve().parent.parent
CARPETA_PLANTILLA = CARPETA_RAG.parent / "plantilla-playwright-pom"
CARPETA_TEMPORAL = Path(tempfile.mkdtemp(prefix="rag-qa-prueba-"))  # fuera de OneDrive

# La base vectorial va a una carpeta temporal para no tocar la del usuario.
os.environ["RAG_QA_DB"] = str(CARPETA_TEMPORAL / "chroma_db")
sys.path.insert(0, str(CARPETA_RAG / "src"))

from rag_qa.herramientas import Herramientas  # noqa: E402
from rag_qa.indice import Indice  # noqa: E402

resultados: list[tuple[str, bool, str]] = []  # (caso, pasó, explicación)


def anotar(caso: str, paso: bool, explicacion: str) -> None:
    """Guarda e imprime el resultado de un caso."""
    resultados.append((caso, paso, explicacion))
    print(f"{'✅' if paso else '❌'} {caso}: {explicacion}")


def programa(nombre: str) -> str:
    """Ruta completa de npm o npx. En Windows son archivos .cmd (npm.cmd, npx.cmd)."""
    con_extension = f"{nombre}.cmd" if os.name == "nt" else nombre
    return shutil.which(con_extension) or con_extension


def ejecutar(argumentos: list[str], carpeta: Path, entorno_extra: dict | None = None, espera: int = 300):
    """Ejecuta npm/npx SIN pasar por la consola (sin shell=True) y devuelve (código, salida).

    `argumentos` es una lista, por ejemplo ["npm", "install"]: así ningún texto se
    interpreta como un comando extra. Si se pasa del tiempo, devuelve (1, "timeout").
    """
    entorno = {**os.environ, "CI": "", **(entorno_extra or {})}
    comando = [programa(argumentos[0]), *argumentos[1:]]
    try:
        proceso = subprocess.run(
            comando, cwd=carpeta, shell=False, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=entorno, timeout=espera,
        )
    except subprocess.TimeoutExpired:
        return 1, "timeout"
    return proceso.returncode, proceso.stdout + proceso.stderr


# npm install sin ejecutar los scripts del package.json (más seguro) y sin avisos extra.
NPM_INSTALL = ["npm", "install", "--no-audit", "--no-fund", "--ignore-scripts"]


def ignorar_al_copiar(carpeta: str, nombres: list[str]) -> set[str]:
    """Para shutil.copytree: qué NO se copia de la plantilla.

    Ni dependencias ni reportes, y tampoco datos sensibles (.env, .env.local, .env.qa...).
    El .env.example sí se copia: es solo un ejemplo sin secretos.
    """
    sin_copiar = {"node_modules", "playwright-report", "test-results"}
    sensibles = {n for n in nombres if (n == ".env" or n.startswith(".env.")) and n != ".env.example"}
    return (sin_copiar & set(nombres)) | sensibles


def quitar_colores(texto: str) -> str:
    """Quita los códigos de color de la consola (ANSI) que trae el texto de Playwright."""
    return re.sub(r"\x1b\[[0-9;]*m", "", texto)


def secciones_devueltas(respuesta: str) -> list[str]:
    """Títulos de sección que devolvió el RAG, en orden ("### 1. `archivo` › sección")."""
    return re.findall(r"^### \d+\. `[^`]+` › (.+)$", respuesta, re.M)


def borrar_carpeta_temporal() -> None:
    """Borra la carpeta temporal. Antes cierra Chroma: en Windows, mientras la base
    está abierta, sus archivos no se pueden borrar."""
    try:
        from chromadb.api.shared_system_client import SharedSystemClient

        for sistema in SharedSystemClient._identifier_to_system.values():
            sistema.stop()
        SharedSystemClient.clear_system_cache()
    except Exception:
        pass  # si cambia la versión de Chroma, se intenta borrar igual
    gc.collect()
    shutil.rmtree(CARPETA_TEMPORAL, ignore_errors=True)
    if CARPETA_TEMPORAL.exists():
        print(f"Aviso: no se pudo borrar del todo la carpeta temporal {CARPETA_TEMPORAL}")


# Todo va dentro de try/finally: la carpeta temporal se borra siempre,
# también si algo falla (por ejemplo, un comando que se pasa del tiempo).
try:
    print(f"Carpeta temporal: {CARPETA_TEMPORAL}")
    print("Cargando el RAG con el modelo de embeddings real (puede tardar la primera vez)...")
    rag = Herramientas(Indice())
    print(rag.reindexar(), "\n")


    # ============================================================ 1. revisar_codigo
    # Cada ejemplo tiene UN anti-patrón. La línea con el problema lleva "// <-- problema".
    EJEMPLOS_MAL_HECHOS = [
        ("Espera fija", "Espera fija", """
test('agrega al carrito', async ({ page }) => {
  await productosPage.agregarAlCarrito('Mochila');
  await page.waitForTimeout(3000); // <-- problema
  await expect(carritoPage.contador).toHaveText('1');
});"""),
        ("Selector frágil (XPath)", "Selector frágil", """
class CarritoPage {
  constructor(page) {
    this.page = page;
    this.pagarButton = page.locator('//div[2]/button[1]'); // <-- problema
  }
}"""),
        ("Contraseña en el código", "contraseña", """
test('login válido', async ({ loginPage }) => {
  await loginPage.abrir();
  await loginPage.login('admin', 'Secreta123');
  const password = 'Secreta123'; // <-- problema
});"""),
        ("if dentro del test", "condicional", """
test('muestra el banner', async ({ homePage }) => {
  await homePage.abrir();
  if (await homePage.banner.isVisible()) { // <-- problema
    await homePage.cerrarBanner();
  }
});"""),
        ("URL completa quemada", "URL completa", """
test('abre el login', async ({ page }) => {
  await page.goto('https://mi-app-qa.empresa.com/login'); // <-- problema
});"""),
        ("Aserción sin reintento", "Aserción sin reintento", """
test('ve el título', async ({ homePage }) => {
  await homePage.abrir();
  expect(await homePage.titulo.isVisible()).toBe(true); // <-- problema
});"""),
        ("Clic con force: true", "force", """
class LoginPage {
  async login(usuario, clave) {
    await this.ingresarButton.click({ force: true }); // <-- problema
  }
}"""),
        ("expect dentro del Page Object", "aserci", """
class LoginPage {
  async validarError(mensaje) {
    await expect(this.mensajeError).toHaveText(mensaje); // <-- problema
  }
}"""),
    ]


    def lineas_senales(respuesta: str) -> list[str]:
        """Las líneas del bloque "Señales detectadas automáticamente"."""
        bloque = respuesta.split("## Señales detectadas automáticamente", 1)[-1].split("\n## ", 1)[0]
        return [l for l in bloque.splitlines() if l.startswith("- ")]


    print("== 1. revisar_codigo ==")
    for nombre, palabra_clave, codigo in EJEMPLOS_MAL_HECHOS:
        codigo = codigo.strip("\n")
        linea_problema = next(n for n, l in enumerate(codigo.splitlines(), 1) if "<-- problema" in l)
        senales = lineas_senales(rag.revisar_codigo(codigo))
        encontrada = [s for s in senales if palabra_clave.lower() in s.lower()]
        if encontrada and str(linea_problema) in encontrada[0].split("línea(s)")[-1]:
            anotar(f"revisar: {nombre}", True, f"detectado en la línea {linea_problema}")
        elif encontrada:
            anotar(f"revisar: {nombre}", False, f"detectado pero en otra línea: {encontrada[0]} (esperada {linea_problema})")
        else:
            anotar(f"revisar: {nombre}", False, f"no lo detectó. Señales: {senales or 'ninguna'}")

    # Código bien hecho: los archivos de la plantilla oficial del equipo no deberían dar errores.
    # Los avisos sí se permiten (por ejemplo, la clave pública de la demo de Sauce Demo
    # sale como "(aviso, no es un error)" para recordar que en una app real va en el .env).
    for archivo in sorted((CARPETA_PLANTILLA / "tests").rglob("*.js")):
        senales = lineas_senales(rag.revisar_codigo(archivo.read_text(encoding="utf-8")))
        errores = [s for s in senales if "(aviso" not in s]
        avisos = len(senales) - len(errores)
        nombre = archivo.relative_to(CARPETA_PLANTILLA).as_posix()
        detalle = "sin falsos positivos" + (f" ({avisos} aviso(s) esperado(s))" if avisos else "")
        anotar(f"revisar (bien hecho): {nombre}", not errores,
               detalle if not errores else f"falso positivo: {errores}")


    # ======================================================== 2. diagnosticar_error
    # Pruebas que fallan A PROPÓSITO. Cada una dice qué sección del catálogo debería salir primero.
    PRUEBAS_QUE_FALLAN = {
        "locator que no existe": ("Error: Timeout en una acción", """
  await page.setContent('<button>Ingresar</button>');
  await page.getByRole('button', { name: 'Entrar' }).click({ timeout: 1000 });"""),
        "dos botones iguales": ("Error: Strict mode violation", """
  await page.setContent('<button>Guardar</button><button>Guardar</button>');
  await page.getByRole('button', { name: 'Guardar' }).click({ timeout: 1000 });"""),
        "aserción que falla": ("Error: Aserción fallida por timeout", """
  await page.setContent('<h1>Inicio</h1>');
  await expect(page.getByRole('heading')).toHaveText('Productos', { timeout: 1000 });"""),
        "URL inválida": ("Error: Cannot navigate to invalid URL", """
  // Una pestaña nueva SIN baseURL: la ruta relativa '/login' no se puede abrir.
  const pestanaSinBaseURL = await (await browser.newContext({ baseURL: undefined })).newPage();
  await pestanaSinBaseURL.goto('/login');"""),
        "dominio mal escrito": ("Error: ERR_NAME_NOT_RESOLVED", """
  // Un espacio en el dominio (error de tipeo): el navegador no encuentra el sitio.
  await page.goto('https://mi app.com/login');"""),
        "servidor apagado": ("Error: ERR_CONNECTION_REFUSED", """
  await page.goto('http://localhost:59999/login');"""),
        "elemento tapado por otro": ("Error: Elemento bloqueado por otro", """
  await page.setContent('<button>Pagar</button>'
    + '<div style="position:fixed;inset:0;background:#0003">Cargando</div>');
  await page.getByRole('button', { name: 'Pagar' }).click({ timeout: 1500 });"""),
        "prueba que tarda demasiado": ("Error: Test timeout exceeded", """
  test.setTimeout(1500);
  await new Promise((listo) => setTimeout(listo, 5000));"""),
        "página cerrada": ("Error: Target page, context or browser has been closed", """
  await page.close();
  await page.getByRole('button').click();"""),
        "import mal hecho": ("Error: LoginPage is not a constructor", """
  const LoginPage = require('../pages/LoginPage');
  new LoginPage(page);"""),
    }


    def crear_spec_que_falla() -> str:
        """Arma un archivo .spec.js con una prueba por cada error que queremos provocar."""
        partes = ["const { test, expect } = require('@playwright/test');\n"]
        for titulo, (_, cuerpo) in PRUEBAS_QUE_FALLAN.items():
            partes.append(f"test('{titulo}', async ({{ page, browser }}) => {{{cuerpo}\n}});\n")
        return "\n".join(partes)


    def error_como_en_consola(error: dict) -> str:
        """Junta el mensaje, el fragmento de código y el stack, como lo ve el QA en la consola."""
        partes = [error.get("message", ""), error.get("snippet", ""), error.get("stack", "").split("\n", 1)[-1]]
        return quitar_colores("\n\n".join(p for p in partes if p))


    VERSION_PLAYWRIGHT = "(no se ejecutó)"


    def errores_reales() -> dict[str, str] | None:
        """Ejecuta las pruebas que fallan y devuelve {título del test: texto del error}."""
        global VERSION_PLAYWRIGHT
        proyecto = CARPETA_TEMPORAL / "proyecto-errores"
        shutil.copytree(CARPETA_PLANTILLA, proyecto, ignore=ignorar_al_copiar)
        codigo, salida = ejecutar(NPM_INSTALL, proyecto)
        if codigo != 0:
            print("   (npm install falló, se usarán errores conocidos)\n", salida[-500:])
            return None
        (proyecto / "tests/specs/fallos-a-proposito.spec.js").write_text(crear_spec_que_falla(), encoding="utf-8")
        # Si la versión de Playwright que instaló npm no tiene sus navegadores descargados en este
        # equipo, se usa la versión que sí los tiene (1.63.0), para no descargar nada.
        _, salida = ejecutar(["npx", "playwright", "test", "fallos-a-proposito", "-g", "URL inválida", "--reporter=line"], proyecto)
        if "Executable doesn't exist" in salida:
            print("   (los navegadores de esa versión no están instalados: se usa @playwright/test@1.63.0)")
            ejecutar([*NPM_INSTALL, "@playwright/test@1.63.0"], proyecto)
        _, version = ejecutar(["npx", "playwright", "--version"], proyecto)
        VERSION_PLAYWRIGHT = version.strip()
        print(f"   Playwright usado: {VERSION_PLAYWRIGHT}")
        reporte = proyecto / "resultado.json"
        ejecutar(["npx", "playwright", "test", "fallos-a-proposito", "--reporter=json", "--workers=4"], proyecto,
                 {"PLAYWRIGHT_JSON_OUTPUT_NAME": str(reporte)})
        if not reporte.exists():
            return None
        errores = {}

        def recorrer(suite):
            for spec in suite.get("specs", []):
                for prueba in spec["tests"]:
                    for r in prueba["results"]:
                        if r.get("errors"):
                            errores[spec["title"]] = error_como_en_consola(r["errors"][0])
            for hija in suite.get("suites", []):
                recorrer(hija)

        for suite in json.loads(reporte.read_text(encoding="utf-8"))["suites"]:
            recorrer(suite)

        # Dos errores más que salen de la consola y no de un test:
        _, salida = ejecutar(["npx", "playwright", "test", "no-existe-este-archivo"], proyecto)
        errores["filtro sin tests"] = quitar_colores(salida.strip())
        navegadores_vacios = CARPETA_TEMPORAL / "sin-navegadores"
        navegadores_vacios.mkdir()
        _, salida = ejecutar(["npx", "playwright", "test", "fallos-a-proposito", "-g", "URL inválida", "--reporter=line"], proyecto,
                             {"PLAYWRIGHT_BROWSERS_PATH": str(navegadores_vacios)})
        errores["navegadores sin instalar"] = quitar_colores(salida.strip())
        return errores


    PRUEBAS_QUE_FALLAN["filtro sin tests"] = ("Error: No tests found", "")
    PRUEBAS_QUE_FALLAN["navegadores sin instalar"] = ("Error: Navegadores no instalados", "")

    # Respaldo por si no hay internet: textos reales conocidos de Playwright.
    ERRORES_CONOCIDOS = {
        "locator que no existe": "Error: locator.click: Timeout 1000ms exceeded.\nCall log:\n  - waiting for getByRole('button', { name: 'Entrar' })",
        "dos botones iguales": "Error: locator.click: Error: strict mode violation: getByRole('button', { name: 'Guardar' }) resolved to 2 elements",
        "aserción que falla": "Error: expect(locator).toHaveText(expected) failed\n\nTimeout: 1000ms",
        "URL inválida": "Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL",
        "servidor apagado": "Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:59999/login",
        "dominio mal escrito": "Error: page.goto: net::ERR_NAME_NOT_RESOLVED at https://mi app.com/login",
        "elemento tapado por otro": "Error: locator.click: Timeout 1500ms exceeded.\n  - <div>Cargando</div> intercepts pointer events",
        "prueba que tarda demasiado": "Test timeout of 1500ms exceeded.",
        "página cerrada": "Error: locator.click: Target page, context or browser has been closed",
        "import mal hecho": "TypeError: LoginPage is not a constructor",
        "filtro sin tests": "Error: No tests found",
        "navegadores sin instalar": "Error: browserType.launch: Executable doesn't exist at C:\\...\\chrome.exe",
    }

    print("\n== 2. diagnosticar_error ==")
    print("   Ejecutando pruebas que fallan a propósito en una copia de la plantilla...")
    errores = errores_reales()
    origen_errores = "reales (ejecutados con Playwright)" if errores else "conocidos (sin ejecutar)"
    errores = errores or ERRORES_CONOCIDOS
    print(f"   Errores {origen_errores}\n")
    TEXTOS_DE_ERROR = errores  # se guardan para el reporte

    for titulo, (seccion_esperada, _) in PRUEBAS_QUE_FALLAN.items():
        texto = errores.get(titulo)
        if not texto:
            anotar(f"diagnosticar: {titulo}", False, "no se pudo provocar el error (la prueba no falló)")
            continue
        respuesta = rag.diagnosticar_error(texto)
        devueltas = secciones_devueltas(respuesta)
        primera = devueltas[0] if devueltas else "(nada)"
        con_aviso = " (pero con aviso de 'no coincide')" if "**Atención:**" in respuesta else ""
        if primera.startswith(seccion_esperada):
            anotar(f"diagnosticar: {titulo}", True, f"primera entrada correcta: {primera}{con_aviso}")
        else:
            lugar = next((i for i, s in enumerate(devueltas, 1) if s.startswith(seccion_esperada)), None)
            detalle = f"la correcta salió en el puesto {lugar}" if lugar else "la correcta no salió"
            anotar(f"diagnosticar: {titulo}", False, f"salió primero '{primera}', {detalle}{con_aviso}")


    # ======================================================= 3. plantilla_proyecto
    print("\n== 3. plantilla_proyecto ==")
    plantilla = rag.plantilla_proyecto()
    archivos = dict(re.findall(r"^## \d+\. Archivo `([^`]+)`\s*\n+```\w*\n(.*?)\n```", plantilla, re.M | re.S))

    for clave in ["package.json", ".env.example", ".gitignore", "playwright.config.js",
                  "tests/pages/LoginPage.js", "tests/pages/HomePage.js", "tests/components/HeaderComponent.js",
                  "tests/fixtures/pages.js", "tests/data/usuarios.js", "tests/specs/login.spec.js"]:
        anotar(f"plantilla trae {clave}", clave in archivos, "incluido" if clave in archivos else "FALTA")

    # ¿Lo que devuelve el RAG es igual a la plantilla real de la carpeta plantilla-playwright-pom?
    distintos = [
        nombre for nombre, contenido in archivos.items()
        if (CARPETA_PLANTILLA / nombre).exists()
        and contenido.strip() != (CARPETA_PLANTILLA / nombre).read_text(encoding="utf-8").strip()
    ]
    anotar("plantilla igual a la carpeta real", not distintos,
           "todos los archivos coinciden" if not distintos else f"difieren: {distintos}")

    # Armar el proyecto con lo que devolvió el RAG y ver si Playwright lo reconoce.
    proyecto_nuevo = CARPETA_TEMPORAL / "proyecto-desde-rag"
    proyecto_nuevo.mkdir()


    def ruta_segura(nombre: str) -> Path | None:
        """Ruta del archivo dentro del proyecto, o None si el nombre intenta salir de la carpeta
        (por ejemplo "../../x" o "C:/x"). El nombre viene del Markdown de la base de conocimiento."""
        destino = (proyecto_nuevo / nombre).resolve()
        if Path(nombre).is_absolute() or not destino.is_relative_to(proyecto_nuevo.resolve()):
            return None
        return destino


    for nombre, contenido in archivos.items():
        destino = ruta_segura(nombre)
        if destino is None:
            anotar(f"plantilla: ruta insegura {nombre}", False, "fuera de la carpeta del proyecto, no se escribió")
            continue
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido + "\n", encoding="utf-8")
    if (proyecto_nuevo / ".env.example").exists():
        shutil.copy(proyecto_nuevo / ".env.example", proyecto_nuevo / ".env")  # paso 1 del .env.example
    codigo, salida = ejecutar(NPM_INSTALL, proyecto_nuevo)
    if codigo == 0:
        codigo, salida = ejecutar(["npx", "playwright", "test", "--list"], proyecto_nuevo)
        total = re.search(r"Total: (\d+) tests? in (\d+) files?", salida)
        anotar("proyecto armado: playwright test --list", codigo == 0 and bool(total),
               f"Playwright lo reconoce ({total.group(0)})" if total else f"no lo reconoce: {salida[-300:]}")
    else:
        anotar("proyecto armado: npm install", False, f"falló la instalación: {salida[-300:]}")


    # ====================================================== 4. buscar_conocimiento
    print("\n== 4. buscar_conocimiento ==")
    PREGUNTAS = [
        ("¿cómo espero a que aparezca un botón sin usar sleep?", ["Regla 3"]),
        ("¿dónde pongo la contraseña del usuario de prueba?", ["Regla 7"]),
        ("¿qué uso para encontrar un botón en la página?", ["Regla 2"]),
        ("¿cómo le pongo nombre a una función del page object?", ["C3", "Regla 4"]),
        ("mi prueba a veces pasa y a veces falla, ¿qué hago?", ["Problema: Prueba inestable"]),
    ]
    for pregunta, esperadas in PREGUNTAS:
        devueltas = secciones_devueltas(rag.buscar_conocimiento(pregunta, max_resultados=3))
        acierto = next((s for s in devueltas if any(s.startswith(e) for e in esperadas)), None)
        anotar(f"buscar: {pregunta}", bool(acierto),
               f"encontró '{acierto}' en el top 3" if acierto else f"top 3 sin la respuesta: {devueltas}")


    # ==================================================================== total
    aprobados = sum(1 for _, paso, _ in resultados if paso)
    print(f"\nTOTAL: {aprobados} ✅ / {len(resultados) - aprobados} ❌ de {len(resultados)} casos")
    print(f"Errores de diagnosticar_error: {origen_errores} - {VERSION_PLAYWRIGHT}")

    # Los textos de error capturados se guardan en la carpeta temporal (se borra al terminar).
    salida_errores = CARPETA_TEMPORAL / "errores-capturados.json"
    salida_errores.write_text(json.dumps(TEXTOS_DE_ERROR, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0 if aprobados == len(resultados) else 1)
finally:
    borrar_carpeta_temporal()
