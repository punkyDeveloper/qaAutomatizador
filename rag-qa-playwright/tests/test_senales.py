"""Pruebas de la detección automática de anti-patrones."""

from pathlib import Path

import pytest

from rag_qa.config import RAIZ_PROYECTO
from rag_qa.senales import detectar


def _nombres(codigo: str) -> set[str]:
    return {s.patron.nombre for s in detectar(codigo)}


@pytest.mark.parametrize(
    "codigo, esperado",
    [
        ("await page.waitForTimeout(3000);", "espera-fija"),
        ("await page.fill('#root > div > input:nth-child(1)', 'x');", "selector-fragil"),
        ("await page.click('xpath=/html/body/div/form/button');", "selector-fragil"),
        ("await page.fill('.css-8x7y2', 'x');", "selector-fragil"),
        ("await page.click('#login');", "selector-en-test"),
        ("await page.goto('https://mi-app.com/login');", "url-quemada"),
        ("expect(await page.isVisible('.dashboard')).toBe(true);", "aserción-sin-reintento"),
        ("await boton.click({ force: true });", "force"),
        ("this.guardar = page.getByRole('button').first();", "first-nth"),
        ("  if (visible) {", "condicional"),
        ("await page.fill('#pass', 'admin123');", "clave-quemada"),
        ("this.btn1 = page.getByRole('button');", "nombre-generico"),
    ],
)
def test_detecta_anti_patron(codigo, esperado):
    assert esperado in _nombres(codigo)


def test_reporta_numero_de_linea():
    senales = detectar("const a = 1;\n\nawait page.waitForTimeout(500);\n")
    assert senales[0].lineas == [3]


def test_ignora_comentarios():
    assert detectar("// Mal: await page.waitForTimeout(3000);") == []


def test_codigo_correcto_de_la_plantilla_no_tiene_senales_graves():
    """La plantilla oficial es el ejemplo bueno: no debe disparar alertas graves."""
    plantilla = RAIZ_PROYECTO.parent / "plantilla-playwright-pom" / "tests"
    if not plantilla.exists():
        pytest.skip("No está la carpeta plantilla-playwright-pom al lado del proyecto")
    graves = {
        "espera-fija", "selector-fragil", "selector-en-test", "url-quemada",
        "aserción-sin-reintento", "force", "expect-en-page-object", "clave-quemada",
    }
    for archivo in Path(plantilla).rglob("*.js"):
        senales = detectar(archivo.read_text(encoding="utf-8"), archivo.as_posix())
        encontrados = {s.patron.nombre for s in senales} & graves
        assert not encontrados, f"{archivo.name}: {encontrados}"


# ---------------------------------------- expect dentro de un Page Object (Regla 1)
PAGE_OBJECT_CON_EXPECT = """class LoginPage {
  async validarError(m) {
    await expect(this.mensajeError).toHaveText(m);
  }
}"""


def test_detecta_expect_en_page_object_por_carpeta_y_por_constructor():
    senales = {s.patron.nombre: s for s in detectar(PAGE_OBJECT_CON_EXPECT, "tests/pages/LoginPage.js")}
    assert senales["expect-en-page-object"].lineas == [3]
    con_constructor = """class LoginPage {
  constructor(page) {}
  async x() { await expect(this.a).toBeVisible(); }
}"""
    assert "expect-en-page-object" in _nombres(con_constructor)


def test_detecta_expect_en_page_object_sin_archivo_y_con_ruta_de_windows():
    assert "expect-en-page-object" in _nombres(PAGE_OBJECT_CON_EXPECT)   # class LoginPage
    sin_nombre_claro = PAGE_OBJECT_CON_EXPECT.replace("LoginPage", "Login")
    nombres = {s.patron.nombre for s in detectar(sin_nombre_claro, "tests\\pages\\Login.js")}
    assert "expect-en-page-object" in nombres


def test_expect_en_el_spec_no_es_senal():
    spec = """test('login', async ({ page }) => {
  await expect(loginPage.mensajeError).toBeVisible();
});"""
    assert "expect-en-page-object" not in _nombres(spec)
    nombres = {s.patron.nombre for s in detectar(spec, "tests/specs/login.spec.js")}
    assert "expect-en-page-object" not in nombres


# ------------------------------------------------- claves de prueba negativa y de demo
def test_clave_de_prueba_negativa_no_es_senal_pero_la_real_si():
    assert "clave-quemada" not in _nombres("    clave: 'clave_incorrecta',")
    assert "clave-quemada" not in _nombres("password: 'wrong_password'")
    assert "clave-quemada" in _nombres("    clave: 'MiClaveReal2024',")


def test_clave_demo_es_aviso_y_no_error():
    senales = {s.patron.nombre: s for s in detectar("const CLAVE_DEMO = 'secret_sauce';")}
    assert "clave-quemada" not in senales
    assert senales["clave-demo"].patron.nivel == "aviso"
