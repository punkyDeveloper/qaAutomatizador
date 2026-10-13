"""Conversión de texto a vectores (embeddings).

- EmbedderModelo: el real. Usa un modelo local de sentence-transformers.
  La primera vez lo descarga (~470 MB) y queda guardado en la carpeta de
  usuario; después funciona sin internet. Ningún documento sale del computador.
- EmbedderHash: sin modelo. Convierte palabras en vectores con un hash.
  Sirve para las pruebas unitarias y como respaldo si el modelo no se puede
  descargar (la búsqueda por palabras clave sigue funcionando bien).
"""

from __future__ import annotations

import hashlib
import math
import sys
from typing import Protocol

from .lexico import tokenizar


class Embedder(Protocol):
    nombre: str

    def documentos(self, textos: list[str]) -> list[list[float]]: ...

    def consulta(self, texto: str) -> list[float]: ...


class EmbedderModelo:
    """Modelo de sentence-transformers (por defecto multilingual-e5-small)."""

    def __init__(self, modelo: str):
        self.nombre = modelo
        self._modelo = None
        # Los modelos E5 necesitan estos prefijos para funcionar bien.
        self._es_e5 = "e5" in modelo.lower()

    def _cargar(self):
        if self._modelo is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:  # pragma: no cover - depende de la instalación
                raise RuntimeError(
                    "Falta la librería sentence-transformers. Ejecuta instalar.bat "
                    "o 'pip install -e .' en la carpeta rag-qa-playwright."
                ) from e
            print(f"[rag-qa] Cargando modelo {self.nombre}...", file=sys.stderr)
            self._modelo = SentenceTransformer(self.nombre, device="cpu")
        return self._modelo

    def _codificar(self, textos: list[str]) -> list[list[float]]:
        vectores = self._cargar().encode(
            textos, normalize_embeddings=True, show_progress_bar=False, batch_size=16
        )
        return [v.tolist() for v in vectores]

    def documentos(self, textos: list[str]) -> list[list[float]]:
        prefijo = "passage: " if self._es_e5 else ""
        return self._codificar([prefijo + t for t in textos])

    def consulta(self, texto: str) -> list[float]:
        prefijo = "query: " if self._es_e5 else ""
        return self._codificar([prefijo + texto])[0]


class EmbedderHash:
    """Vectores por hash de palabras. Determinístico, rápido y sin descargas."""

    def __init__(self, dimension: int = 512):
        self.dimension = dimension
        self.nombre = f"hash-{dimension}"

    def _vector(self, texto: str) -> list[float]:
        v = [0.0] * self.dimension
        for tok in tokenizar(texto):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dimension] += 1.0 if (h >> 64) % 2 else -1.0
        norma = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norma for x in v]

    def documentos(self, textos: list[str]) -> list[list[float]]:
        return [self._vector(t) for t in textos]

    def consulta(self, texto: str) -> list[float]:
        return self._vector(texto)


def crear_embedder(tipo: str, modelo: str) -> Embedder:
    if tipo == "hash":
        return EmbedderHash()
    if tipo == "modelo":
        return EmbedderModelo(modelo)
    raise ValueError(f"RAG_QA_EMBEDDER inválido: '{tipo}'. Usa 'modelo' o 'hash'.")
