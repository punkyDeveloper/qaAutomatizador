"""Pruebas de las 4 funciones del asistente."""

from rag_qa.herramientas import Herramientas

CODIGO_MALO = """
test('login', async ({ page }) => {
  await page.goto('https://mi-app.com/login');
  await page.fill('#root > div > form > input:nth-child(1)', 'admin');
  await page.waitForTimeout(3000);
  expect(await page.isVisible('.dashboard')).toBe(true);
});
"""


# ------------------------------------------------- Función 1: revisar código
def test_revisar_codigo_incluye_formato_y_checklists(herramientas: Herramientas):
    salida = herramientas.revisar_codigo(CODIGO_MALO, "tests/specs/login.spec.js")
    assert "❌ Problema" in salida                       # formato de respuesta
    assert "¿No hay esperas fijas?" in salida            # checklist de reglas
    assert "(C2)" in salida                              # checklist de convenciones
    assert "tests/specs/login.spec.js" in salida
    assert "NUNCA crea, modifica ni borra archivos" in salida  # Función 3: solo sugerir


def test_revisar_codigo_trae_la_regla_de_esperas(herramientas: Herramientas):
    salida = herramientas.revisar_codigo(CODIGO_MALO)
    assert "Regla 3: Nada de esperas fijas" in salida


def test_revisar_codigo_vacio(herramientas: Herramientas):
    assert "No se recibió código" in herramientas.revisar_codigo("  ")


# ------------------------------------------- Función 2: diagnosticar errores
ERROR_TIMEOUT = """Error: locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Ingresar' })
    at LoginPage.login (tests/pages/LoginPage.js:18:31)
"""


def test_diagnosticar_error_conocido(herramientas: Herramientas):
    salida = herramientas.diagnosticar_error(ERROR_TIMEOUT)
    assert "Error: Timeout en una acción" in salida
    assert "coincidencia alta" in salida
    assert "🔴 Qué pasó" in salida                       # formato de respuesta
    assert "stack trace" in salida                       # cómo ubicar archivo y línea


def test_diagnosticar_error_conocido_no_muestra_aviso(herramientas: Herramientas):
    assert "**Atención:**" not in herramientas.diagnosticar_error(ERROR_TIMEOUT)


def test_diagnosticar_strict_mode(herramientas: Herramientas):
    salida = herramientas.diagnosticar_error(
        "Error: locator.click: Error: strict mode violation: getByRole('button') resolved to 2 elements"
    )
    entradas = salida.split("## Entradas del catálogo de errores")[1]
    assert entradas.index("Strict mode violation") < 200


def test_diagnosticar_error_desconocido_avisa(herramientas: Herramientas):
    salida = herramientas.diagnosticar_error("Segmentation fault in quantum flux capacitor")
    assert "**Atención:**" in salida


def test_diagnosticar_incluye_codigo_relacionado(herramientas: Herramientas):
    salida = herramientas.diagnosticar_error(ERROR_TIMEOUT, "await this.ingresarButton.click();")
    assert "await this.ingresarButton.click();" in salida


def test_diagnosticar_error_vacio(herramientas: Herramientas):
    assert "No se recibió ningún error" in herramientas.diagnosticar_error("")


# ----------------------------------------------- Función 4: plantilla
def test_plantilla_incluye_todos_los_archivos(herramientas: Herramientas):
    salida = herramientas.plantilla_proyecto()
    for archivo in (
        "package.json",
        ".env.example",
        "playwright.config.js",
        "tests/pages/LoginPage.js",
        "tests/components/HeaderComponent.js",
        "tests/fixtures/pages.js",
        "tests/specs/login.spec.js",
    ):
        assert archivo in salida, f"falta {archivo}"
    assert "TODO:" in salida and "DEMO:" in salida
    assert "Proyecto desde cero" in salida               # instrucciones de modo


# ------------------------------------------------------ buscar y estado
def test_buscar_conocimiento(herramientas: Herramientas):
    salida = herramientas.buscar_conocimiento("Cannot navigate to invalid URL", "errores", 3)
    assert "Error: Cannot navigate to invalid URL" in salida


def test_buscar_categoria_invalida(herramientas: Herramientas):
    assert "Categoría inválida" in herramientas.buscar_conocimiento("x", "inventada")


def test_buscar_limita_max_resultados(herramientas: Herramientas):
    salida = herramientas.buscar_conocimiento("playwright", max_resultados=50)
    assert salida.count("\n### ") <= 10


def test_estado_y_reindexar(herramientas: Herramientas):
    total = len(herramientas.indice.documentos)
    assert f"Documentos: {total}" in herramientas.estado()
    assert f"Índice reconstruido: {total} documentos" in herramientas.reindexar()
