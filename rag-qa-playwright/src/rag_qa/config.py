"""Configuración del RAG.

Todo tiene un valor por defecto que funciona sin tocar nada. Si hace falta
cambiar algo, se usan variables de entorno:

- RAG_QA_KB        Carpeta de la base de conocimiento.
                   Por defecto: <proyecto>/knowledge-base
- RAG_QA_DB        Carpeta donde se guarda la base vectorial (Chroma).
                   Por defecto: <carpeta de usuario>/.rag-qa-playwright/chroma_db
                   (fuera de OneDrive a propósito: OneDrive puede bloquear
                   los archivos de la base de datos mientras se usan).
- RAG_QA_MODELO    Modelo de embeddings de sentence-transformers.
                   Por defecto: intfloat/multilingual-e5-small (entiende español).
- RAG_QA_EMBEDDER  "modelo" (por defecto) o "hash" (sin modelo: solo para
                   pruebas o si el modelo no se puede descargar).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# src/rag_qa/config.py -> raíz del proyecto rag-qa-playwright
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

MODELO_POR_DEFECTO = "intfloat/multilingual-e5-small"


def _ruta_env(nombre: str, por_defecto: Path) -> Path:
    valor = os.environ.get(nombre)
    return Path(valor).expanduser().resolve() if valor else por_defecto


@dataclass(frozen=True)
class Config:
    kb_dir: Path = field(
        default_factory=lambda: _ruta_env("RAG_QA_KB", RAIZ_PROYECTO / "knowledge-base")
    )
    db_dir: Path = field(
        default_factory=lambda: _ruta_env(
            "RAG_QA_DB", Path.home() / ".rag-qa-playwright" / "chroma_db"
        )
    )
    modelo: str = field(
        default_factory=lambda: os.environ.get("RAG_QA_MODELO", MODELO_POR_DEFECTO)
    )
    embedder: str = field(
        default_factory=lambda: os.environ.get("RAG_QA_EMBEDDER", "modelo")
    )
