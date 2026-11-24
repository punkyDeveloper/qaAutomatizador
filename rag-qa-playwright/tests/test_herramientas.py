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


def test_diagnosticar_con_salida_completa_de_consola_usa_la_linea_del_error(herramientas: Herramientas):
    consola = f"""Running 1 test using 1 worker

  ✘  1 [chromium] › tests/specs/login.spec.js:5:3 › login (30.0s)

  1) [chromium] › tests/specs/login.spec.js:5:3 › login ───────

    tests/specs/login.spec.js:5:3

{ERROR_TIMEOUT}
  1 failed
"""
    salida = herramientas.diagnosticar_error(consola)
    assert "Mensaje principal: `Error: locator.click: Timeout 30000ms exceeded.`" in salida


# Salida real capturada de Playwright (elemento tapado): el mensaje solo dice "Timeout exceeded";
# la causa está en el Call log.
ERROR_ELEMENTO_TAPADO = """TimeoutError: locator.click: Timeout 1500ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Pagar' })
    - locator resolved to <button>Pagar</button>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div>Cargando</div> intercepts pointer events
    - retrying click action
    - waiting 20ms
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <div>Cargando</div> intercepts pointer events
    - retrying click action
      - waiting 500ms


  28 |   await page.setContent('<button>Pagar</button>'
  29 |     + '<div style="position:fixed;inset:0;background:#0003">Cargando</div>');
> 30 |   await page.getByRole('button', { name: 'Pagar' }).click({ timeout: 1500 });
     |                                                     ^
  31 | });
    at tests/specs/fallos-a-proposito.spec.js:30:53
"""


def test_diagnosticar_elemento_tapado_usa_la_pista_del_call_log(herramientas: Herramientas):
    salida = herramientas.diagnosticar_error(ERROR_ELEMENTO_TAPADO)
    entradas = salida.split("## Entradas del catálogo de errores")[1]
    primera = entradas.split("### 2.")[0]
    assert "Elemento bloqueado por otro" in primera
    assert "Pistas del Call log: `intercepts pointer events`" in salida
    assert "**Atención:**" not in salida


def test_revisar_page_object_con_expect_lo_marca(herramientas: Herramientas):
    page_object = """class LoginPage {
  async validarError(m) {
    await expect(this.mensajeError).toHaveText(m);
  }
}"""
    salida = herramientas.revisar_codigo(page_object, "tests/pages/LoginPage.js")
    assert "Aserción (expect) dentro del Page Object" in salida
    assert "línea(s) 3" in salida


def test_revisar_clave_demo_sale_como_aviso(herramientas: Herramientas):
    salida = herramientas.revisar_codigo("const CLAVE_DEMO = 'secret_sauce';", "tests/data/usuarios.js")
    assert "(aviso, no es un error) Clave de demo" in salida
    assert "Posible contraseña escrita en el código" not in salida


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


# Bug 5: buscar_conocimiento acota max_resultados igual que la CLI y acepta consulta None.
def test_buscar_conocimiento_casos_borde(herramientas: Herramientas):
    con_cero = herramientas.buscar_conocimiento("locator timeout", max_resultados=0)
    con_uno = herramientas.buscar_conocimiento("locator timeout", max_resultados=1)
    assert con_cero == con_uno
    assert isinstance(herramientas.buscar_conocimiento(None, max_resultados=None), str)
