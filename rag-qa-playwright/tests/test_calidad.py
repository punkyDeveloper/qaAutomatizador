"""Evaluación de calidad del RAG (Paso 5).

Preguntas reales con la sección que DEBERÍA encontrar el RAG entre sus 3
primeros resultados.

- Los mensajes de error exactos se prueban siempre (con y sin modelo).
- Las preguntas en lenguaje natural necesitan el modelo real de embeddings:
  se ejecutan cuando el modelo ya está descargado (lo hace instalar.bat).

Para agregar un caso nuevo, basta con añadir una línea a la lista que corresponda.
"""

from __future__ import annotations

import pytest

from rag_qa.config import MODELO_POR_DEFECTO, Config
from rag_qa.embeddings import EmbedderModelo
from rag_qa.indice import Indice

from .conftest import KB_REAL

TOP = 3

# (consulta, categoría para filtrar o None, inicios de sección aceptados)
CASOS_ERRORES_EXACTOS = [
    ("Error: locator.click: Timeout 30000ms exceeded.", None, ["Error: Timeout en una acción"]),
    ("strict mode violation: getByRole('button') resolved to 2 elements", None, ["Error: Strict mode violation"]),
    ("page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL", None, ["Error: Cannot navigate"]),
    ("page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/login", None, ["Error: ERR_CONNECTION_REFUSED"]),
    ("browserType.launch: Executable doesn't exist at /ms-playwright/chromium", None, ["Error: Navegadores no instalados"]),
    ("<div class=\"overlay\"></div> intercepts pointer events", None, ["Error: Elemento bloqueado"]),
    ("locator.fill: Target page, context or browser has been closed", None, ["Error: Target page"]),
    ("TypeError: LoginPage is not a constructor", None, ["Error: LoginPage is not a constructor"]),
    ("Test timeout of 30000ms exceeded.", "errores", ["Error: Test timeout exceeded"]),
    ("Error: No tests found", None, ["Error: No tests found"]),
    ("Timed out 5000ms waiting for expect(locator).toHaveText(expected)", None, ["Error: Aserción fallida por timeout"]),
    ("await page.waitForTimeout(3000)", "buenas-practicas", ["Regla 3"]),
]

CASOS_LENGUAJE_NATURAL = [
    ("¿Dónde van las aserciones, en el Page Object o en el test?", None, ["Regla 1"]),
    ("¿Cómo debo nombrar el archivo de un Page Object?", None, ["C1"]),
    ("¿Qué tipo de locator debo usar primero?", None, ["Regla 2"]),
    ("Mi prueba a veces pasa y a veces falla", None, ["Problema: Prueba inestable"]),
    ("No quiero iniciar sesión por la interfaz en cada test", None, ["Regla 6", "Error: Test timeout"]),
    ("¿Dónde pongo la contraseña del usuario de pruebas?", None, ["Regla 7", "3. Archivo `.env.example`", "10. Archivo `tests/data"]),
    ("El test pasa en verde pero no está validando nada", None, ["Error: Prueba que pasa aunque debería fallar"]),
    ("Quiero crear un proyecto de pruebas nuevo desde cero", None, ["Función 4", "Paso previo", "1. Estructura", "Introducción"]),
    ("¿Cómo se deben llamar los tests?", None, ["C4"]),
    ("El encabezado del sitio se repite en todas las páginas", None, ["Regla 5", "7. Archivo `tests/components"]),
    ("El botón no aparece y la prueba se queda esperando", "errores", ["Error: Timeout en una acción", "Error: Elemento bloqueado", "Error: Aserción fallida"]),
    ("¿Cómo registro un page object nuevo en los fixtures?", None, ["C6", "9. Archivo `tests/fixtures"]),
]


def _secciones(indice: Indice, consulta: str, categoria: str | None) -> list[str]:
    resultados = indice.buscar(consulta, [categoria] if categoria else None, TOP)
    return [r.fragmento.seccion for r in resultados]


def _verificar(indice, consulta, categoria, aceptadas):
    encontradas = _secciones(indice, consulta, categoria)
    assert any(s.startswith(a) for s in encontradas for a in aceptadas), (
        f"\nConsulta: {consulta}\nEsperaba: {aceptadas}\nObtuvo:   {encontradas}"
    )


# ------------------------------------------------------- sin modelo (hash)
@pytest.mark.parametrize("consulta, categoria, aceptadas", CASOS_ERRORES_EXACTOS)
def test_errores_exactos_sin_modelo(indice, consulta, categoria, aceptadas):
    _verificar(indice, consulta, categoria, aceptadas)


# ------------------------------------------------------ con modelo real
@pytest.fixture(scope="module")
def indice_modelo(tmp_path_factory):
    try:
        from sentence_transformers import SentenceTransformer

        SentenceTransformer(MODELO_POR_DEFECTO, device="cpu", local_files_only=True)
    except Exception as e:  # modelo o librería no disponibles
        pytest.skip(f"Modelo real no disponible ({type(e).__name__}). Ejecuta instalar.bat primero.")
    config = Config(kb_dir=KB_REAL, db_dir=tmp_path_factory.mktemp("db_modelo"), embedder="modelo")
    indice = Indice(config, EmbedderModelo(MODELO_POR_DEFECTO))
    indice.preparar()
    return indice


@pytest.mark.modelo
@pytest.mark.parametrize("consulta, categoria, aceptadas", CASOS_ERRORES_EXACTOS)
def test_errores_exactos_con_modelo(indice_modelo, consulta, categoria, aceptadas):
    _verificar(indice_modelo, consulta, categoria, aceptadas)


# Con preguntas en lenguaje natural se mide el porcentaje de aciertos del
# conjunto completo (como se evalúa un buscador), no cada pregunta por separado.
MINIMO_ACIERTOS = 0.80


@pytest.mark.modelo
def test_lenguaje_natural_con_modelo(indice_modelo):
    fallos = []
    for consulta, categoria, aceptadas in CASOS_LENGUAJE_NATURAL:
        encontradas = _secciones(indice_modelo, consulta, categoria)
        if not any(s.startswith(a) for s in encontradas for a in aceptadas):
            fallos.append(f"- {consulta}\n    esperaba {aceptadas}\n    obtuvo   {encontradas}")
    aciertos = 1 - len(fallos) / len(CASOS_LENGUAJE_NATURAL)
    print(f"\nAciertos en lenguaje natural: {aciertos:.0%}")
    assert aciertos >= MINIMO_ACIERTOS, (
        f"Aciertos {aciertos:.0%} (mínimo {MINIMO_ACIERTOS:.0%}). Fallos:\n" + "\n".join(fallos)
    )
