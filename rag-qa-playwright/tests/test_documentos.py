"""Pruebas de lectura y división de documentos (Paso 3)."""

from pathlib import Path

import pytest

from rag_qa.documentos import (
    ErrorDocumento,
    cargar_documentos,
    dividir_secciones,
    fragmentar,
    fragmentar_todo,
    huella,
    leer_metadatos,
)
from rag_qa.herramientas import CATEGORIAS

from .conftest import KB_REAL


def test_lee_metadatos_y_cuerpo():
    meta, cuerpo = leer_metadatos("---\nid: js-x-001\ncategoria: errores\n---\n# Título\n")
    assert meta == {"id": "js-x-001", "categoria": "errores"}
    assert cuerpo.startswith("# Título")


def test_acepta_saltos_de_linea_de_windows():
    meta, _ = leer_metadatos("---\r\nid: js-x-001\r\n---\r\n# T\r\n")
    assert meta["id"] == "js-x-001"


def test_documento_sin_metadatos_falla():
    with pytest.raises(ErrorDocumento):
        leer_metadatos("# Sin metadatos")


def test_ignora_titulos_dentro_de_bloques_de_codigo():
    cuerpo = "# Doc\n\n## Sección A\ntexto\n```bash\n## esto es un comentario\n```\n## Sección B\nmás"
    titulo, _, secciones = dividir_secciones(cuerpo)
    assert titulo == "Doc"
    assert [s for s, _ in secciones] == ["Sección A", "Sección B"]
    assert "## esto es un comentario" in secciones[0][1]


def test_quita_separadores_al_final_de_cada_seccion():
    _, _, secciones = dividir_secciones("# D\n## A\ncontenido\n\n---\n\n## B\nx")
    assert secciones[0][1] == "contenido"


def test_carga_todos_los_documentos_reales():
    docs = cargar_documentos(KB_REAL)
    assert len(docs) == len(list(KB_REAL.rglob("*.md")))
    assert len({d.id for d in docs}) == len(docs), "hay ids repetidos"
    for d in docs:
        assert d.categoria in CATEGORIAS, f"{d.archivo} tiene categoría desconocida"
        assert d.titulo, f"{d.archivo} no tiene título"


def test_cada_fragmento_tiene_metadatos_y_titulo_del_documento():
    fragmentos = fragmentar_todo(cargar_documentos(KB_REAL))
    assert len(fragmentos) > 30
    assert len({f.id for f in fragmentos}) == len(fragmentos)
    for f in fragmentos:
        assert f.contenido.strip()
        assert f.metadatos["titulo_doc"] in f.texto
        for clave in ("doc_id", "archivo", "categoria", "seccion"):
            assert f.metadatos[clave]


def test_catalogo_de_errores_tiene_una_seccion_por_error():
    docs = [d for d in cargar_documentos(KB_REAL) if d.categoria == "errores"]
    secciones = [f.seccion for f in fragmentar(docs[0])]
    for esperado in ("Error: Timeout en una acción", "Error: Strict mode violation (varios elementos)"):
        assert esperado in secciones


def test_huella_cambia_si_cambia_un_documento(kb_copia: Path):
    antes = huella(cargar_documentos(kb_copia))
    archivo = next(kb_copia.rglob("convenciones-equipo.md"))
    archivo.write_text(archivo.read_text(encoding="utf-8") + "\n## Nueva\nx\n", encoding="utf-8")
    assert huella(cargar_documentos(kb_copia)) != antes


def test_huella_depende_del_modelo():
    docs = cargar_documentos(KB_REAL)
    assert huella(docs, "modelo-a") != huella(docs, "modelo-b")


def test_id_repetido_falla(kb_copia: Path):
    original = next(kb_copia.rglob("convenciones-equipo.md"))
    (kb_copia / "general" / "copia.md").write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ErrorDocumento, match="id repetido"):
        cargar_documentos(kb_copia)


def test_carpeta_inexistente_falla(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        cargar_documentos(tmp_path / "no-existe")
