"""Pruebas de lectura y división de documentos (Paso 3)."""

from pathlib import Path

import pytest

from rag_qa.documentos import (
    MAX_BYTES_DOCUMENTO,
    ErrorDocumento,
    cargar_documentos,
    dividir_secciones,
    fragmentar,
    fragmentar_todo,
    huella,
    leer_metadatos,
    _es_documento_seguro,
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


def test_error_de_formato_dice_el_archivo_y_como_arreglarlo(kb_copia: Path):
    (kb_copia / "general" / "roto.md").write_text("# Sin metadatos\n## A\nx\n", encoding="utf-8")
    with pytest.raises(ErrorDocumento, match=r"roto\.md.*validar_documentos\.py"):
        cargar_documentos(kb_copia)


def test_ignora_documentos_enormes(kb_copia: Path):
    original = next(kb_copia.rglob("convenciones-equipo.md"))
    texto = original.read_text(encoding="utf-8").replace("gen-convenciones-001", "gen-enorme-001")
    relleno = "x" * (MAX_BYTES_DOCUMENTO + 1)
    (kb_copia / "general" / "enorme.md").write_text(texto + relleno, encoding="utf-8")
    archivos = [d.archivo for d in cargar_documentos(kb_copia)]
    assert "general/enorme.md" not in archivos


def test_ignora_enlaces_simbolicos_que_salen_de_la_base(kb_copia: Path, tmp_path: Path):
    # Un .md fuera de la base, con un enlace simbólico dentro de ella que apunta a él.
    original = next(kb_copia.rglob("convenciones-equipo.md"))
    externo = tmp_path / "secreto.md"
    externo.write_text(
        original.read_text(encoding="utf-8").replace("gen-convenciones-001", "gen-externo-001"),
        encoding="utf-8",
    )
    enlace = kb_copia / "general" / "enlace.md"
    try:
        enlace.symlink_to(externo)
    except OSError:
        pytest.skip("Este Windows no permite crear enlaces simbólicos sin permisos de administrador")
    archivos = [d.archivo for d in cargar_documentos(kb_copia)]
    assert "general/enlace.md" not in archivos


def test_archivo_fuera_de_la_base_no_es_seguro(kb_copia: Path, tmp_path: Path):
    externo = tmp_path / "fuera.md"
    externo.write_text("---\nid: gen-fuera-001\n---\n# Fuera\n## A\nx\n", encoding="utf-8")
    assert not _es_documento_seguro(externo, kb_copia)
    assert _es_documento_seguro(next(kb_copia.rglob("convenciones-equipo.md")), kb_copia)


# Bug 3: un .md que no está en UTF-8 da un ErrorDocumento con el nombre del archivo.
def test_documento_no_utf8_da_error_claro(tmp_path: Path):
    (tmp_path / "ansi.md").write_bytes("---\nid: gen-x-001\n---\n# Año\n## Sección\nñ\n".encode("latin-1"))
    with pytest.raises(ErrorDocumento, match=r"ansi\.md.*guárdalo como UTF-8"):
        cargar_documentos(tmp_path)


# Bug 4: un bloque de metadatos vacío está cerrado (no debe decir "no está cerrado").
def test_bloque_de_metadatos_vacio_se_lee():
    metadatos, cuerpo = leer_metadatos("---\n---\n# T\n")
    assert metadatos == {} and cuerpo == "# T\n"
