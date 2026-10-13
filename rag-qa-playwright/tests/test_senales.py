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
    graves = {"espera-fija", "selector-fragil", "selector-en-test", "url-quemada", "aserción-sin-reintento", "force"}
    for archivo in Path(plantilla).rglob("*.js"):
        encontrados = _nombres(archivo.read_text(encoding="utf-8")) & graves
        assert not encontrados, f"{archivo.name}: {encontrados}"
