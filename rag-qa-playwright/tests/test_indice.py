"""Pruebas del índice: Chroma + búsqueda híbrida (Pasos 3 y 4)."""

from pathlib import Path

from rag_qa.config import Config
from rag_qa.documentos import cargar_documentos, fragmentar_todo
from rag_qa.indice import Indice

from .conftest import KB_REAL, EmbedderContador


def test_indexa_todas_las_secciones(indice: Indice):
    esperado = len(fragmentar_todo(cargar_documentos(KB_REAL)))
    assert indice.total_fragmentos == esperado
    assert indice.reconstrucciones == 1
    assert (indice.config.db_dir / "chroma.sqlite3").exists()


def test_encuentra_error_por_mensaje_exacto(indice: Indice):
    r = indice.buscar("Error: locator.click: Timeout 30000ms exceeded.")
    assert r[0].fragmento.seccion == "Error: Timeout en una acción"


def test_filtra_por_categoria(indice: Indice):
    resultados = indice.buscar("POM page object locators", categorias=["convenciones"], max_resultados=10)
    assert resultados
    assert all(r.fragmento.metadatos["categoria"] == "convenciones" for r in resultados)


def test_respeta_max_resultados(indice: Indice):
    assert len(indice.buscar("playwright", max_resultados=3)) == 3


def test_consulta_vacia_no_devuelve_nada(indice: Indice):
    assert indice.buscar("   ") == []


def test_categoria_sin_documentos_no_devuelve_nada(indice: Indice):
    assert indice.buscar("algo", categorias=["no-existe"]) == []


def test_resultados_ordenados_por_puntaje(indice: Indice):
    r = indice.buscar("esperas fijas waitForTimeout", max_resultados=5)
    puntajes = [x.puntaje for x in r]
    assert puntajes == sorted(puntajes, reverse=True)


def test_no_reindexa_si_nada_cambio(config: Config):
    """Un segundo arranque reutiliza los vectores guardados en Chroma."""
    e1 = EmbedderContador()
    Indice(config, e1).preparar()
    assert e1.textos_vectorizados > 0

    e2 = EmbedderContador()
    i2 = Indice(config, e2)
    assert i2.preparar() is False
    assert e2.textos_vectorizados == 0
    assert i2.buscar("strict mode violation")[0].fragmento.seccion.startswith("Error: Strict mode")


def test_reindexa_solo_cuando_cambia_un_documento(kb_copia: Path, tmp_path: Path):
    config = Config(kb_dir=kb_copia, db_dir=tmp_path / "db2", embedder="hash")
    indice = Indice(config, EmbedderContador())
    indice.preparar()
    antes = indice.total_fragmentos

    archivo = next(kb_copia.rglob("playwright-errores-comunes.md"))
    archivo.write_text(
        archivo.read_text(encoding="utf-8")
        + "\n---\n\n## Error: Mensaje inventado zxqw\n\n**Mensaje:** zxqw plorf.\n",
        encoding="utf-8",
    )
    resultados = indice.buscar("zxqw plorf")  # buscar detecta el cambio solo
    assert indice.reconstrucciones == 2
    assert indice.total_fragmentos == antes + 1
    assert resultados[0].fragmento.seccion == "Error: Mensaje inventado zxqw"


def test_reindexar_forzado(indice: Indice):
    assert indice.preparar(forzar=True) is True
    assert indice.reconstrucciones == 2
