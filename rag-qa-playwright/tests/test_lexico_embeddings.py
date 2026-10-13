"""Pruebas de la búsqueda por palabras clave y de los embeddings sin modelo."""

import math

import pytest

from rag_qa.embeddings import EmbedderHash, EmbedderModelo, crear_embedder
from rag_qa.lexico import BM25, tokenizar


def test_tokenizar_quita_tildes_y_mayusculas():
    assert "contrasena" in tokenizar("Contraseña")


def test_tokenizar_separa_camel_case():
    tokens = tokenizar("waitForTimeout")
    assert {"waitfortimeout", "wait", "timeout"} <= set(tokens)


def test_tokenizar_agrega_raiz_aproximada():
    assert "nombr~" in tokenizar("nombro") and "nombr~" in tokenizar("nombres")


def test_tokenizar_ignora_palabras_vacias():
    assert tokenizar("de la el con") == []


def test_bm25_prefiere_el_texto_con_las_palabras():
    bm = BM25(["strict mode violation varios elementos", "timeout exceeded", "otro texto"])
    p = bm.puntajes("strict mode violation")
    assert p[0] > p[1] and p[0] > p[2]
    assert p[2] == 0


def test_embedder_hash_es_normalizado_y_deterministico():
    e = EmbedderHash()
    v1, v2 = e.consulta("hola mundo"), e.consulta("hola mundo")
    assert v1 == v2
    assert math.isclose(sum(x * x for x in v1), 1.0, rel_tol=1e-6)


def test_embedder_hash_textos_parecidos_son_mas_cercanos():
    e = EmbedderHash()
    a, b, c = e.documentos(["timeout en click", "timeout en fill", "nombres de archivos"])
    dot = lambda x, y: sum(i * j for i, j in zip(x, y))
    assert dot(a, b) > dot(a, c)


def test_crear_embedder():
    assert isinstance(crear_embedder("hash", "x"), EmbedderHash)
    assert isinstance(crear_embedder("modelo", "x"), EmbedderModelo)
    with pytest.raises(ValueError):
        crear_embedder("otro", "x")


def test_modelo_e5_usa_prefijos():
    e = EmbedderModelo("intfloat/multilingual-e5-small")
    capturado = []
    e._codificar = lambda textos: capturado.extend(textos) or [[0.0] for _ in textos]
    e.documentos(["doc"])
    e.consulta("pregunta")
    assert capturado == ["passage: doc", "query: pregunta"]
