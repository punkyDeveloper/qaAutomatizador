"""Configuración compartida de las pruebas.

Las pruebas unitarias usan el embedder "hash" (sin modelo): son rápidas y no
necesitan internet. Las pruebas marcadas con @pytest.mark.modelo usan el
modelo real y se omiten si todavía no está descargado.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from rag_qa.config import RAIZ_PROYECTO, Config
from rag_qa.embeddings import EmbedderHash
from rag_qa.herramientas import Herramientas
from rag_qa.indice import Indice

KB_REAL = RAIZ_PROYECTO / "knowledge-base"


class EmbedderContador(EmbedderHash):
    """Embedder hash que cuenta cuántos textos vectoriza (para medir reindexaciones)."""

    def __init__(self):
        super().__init__()
        self.textos_vectorizados = 0

    def documentos(self, textos):
        self.textos_vectorizados += len(textos)
        return super().documentos(textos)


@pytest.fixture
def kb_copia(tmp_path: Path) -> Path:
    """Copia de la base de conocimiento real, para poder modificarla en las pruebas."""
    destino = tmp_path / "knowledge-base"
    shutil.copytree(KB_REAL, destino)
    return destino


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(kb_dir=KB_REAL, db_dir=tmp_path / "db", embedder="hash")


@pytest.fixture
def indice(config: Config) -> Indice:
    i = Indice(config, EmbedderContador())
    i.preparar()
    return i


@pytest.fixture
def herramientas(indice: Indice) -> Herramientas:
    return Herramientas(indice)
