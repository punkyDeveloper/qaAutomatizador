"""Índice del RAG: guarda los vectores en Chroma y hace la búsqueda híbrida.

Búsqueda híbrida = búsqueda por significado (vectores) + búsqueda por palabras
clave (BM25), combinadas con Reciprocal Rank Fusion (RRF). Así funciona bien
tanto con preguntas en lenguaje natural ("¿cómo nombro un page object?") como
con mensajes de error exactos ("strict mode violation").

El índice se reconstruye solo cuando cambia algún documento de knowledge-base/.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from .config import Config
from .documentos import Documento, Fragmento, cargar_documentos, fragmentar_todo, huella
from .embeddings import Embedder, crear_embedder
from .lexico import BM25

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

NOMBRE_COLECCION = "knowledge_base"
RRF_K = 60


@dataclass
class Resultado:
    fragmento: Fragmento
    puntaje: float          # puntaje combinado (más alto = más relevante)
    similitud: float        # similitud por vectores (-1 a 1)
    puntaje_lexico: float   # puntaje BM25 (0 = ninguna palabra en común)


class Indice:
    def __init__(self, config: Config | None = None, embedder: Embedder | None = None):
        self.config = config or Config()
        self.embedder = embedder or crear_embedder(self.config.embedder, self.config.modelo)
        self.documentos: list[Documento] = []
        self._fragmentos: list[Fragmento] = []
        self._vectores = None
        self._bm25: BM25 | None = None
        self._huella: str | None = None
        self.reconstrucciones = 0  # útil para pruebas y diagnóstico

    # ------------------------------------------------------------------ Chroma
    def _cliente(self):
        import chromadb
        from chromadb.config import Settings

        self.config.db_dir.mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=str(self.config.db_dir), settings=Settings(anonymized_telemetry=False)
        )

    # --------------------------------------------------------------- preparar
    def preparar(self, forzar: bool = False) -> bool:
        """Carga el índice, reconstruyéndolo si los documentos cambiaron.

        Devuelve True si tuvo que reconstruir (generar vectores de nuevo).
        """
        import numpy as np

        documentos = cargar_documentos(self.config.kb_dir)
        nueva_huella = huella(documentos, self.embedder.nombre)
        if not forzar and nueva_huella == self._huella:
            return False

        fragmentos = fragmentar_todo(documentos)
        cliente = self._cliente()
        coleccion = None
        try:
            coleccion = cliente.get_collection(NOMBRE_COLECCION)
        except Exception:
            coleccion = None

        reconstruir = (
            forzar
            or coleccion is None
            or (coleccion.metadata or {}).get("huella") != nueva_huella
            or coleccion.count() != len(fragmentos)
        )
        if reconstruir:
            print(
                f"[rag-qa] Indexando {len(fragmentos)} secciones de {len(documentos)} documentos...",
                file=sys.stderr,
            )
            if coleccion is not None:
                cliente.delete_collection(NOMBRE_COLECCION)
            coleccion = cliente.create_collection(
                NOMBRE_COLECCION,
                metadata={"huella": nueva_huella, "embedder": self.embedder.nombre},
            )
            vectores = self.embedder.documentos([f.texto for f in fragmentos])
            coleccion.add(
                ids=[f.id for f in fragmentos],
                embeddings=vectores,
                documents=[f.texto for f in fragmentos],
                metadatas=[f.metadatos for f in fragmentos],
            )
            self.reconstrucciones += 1

        guardado = coleccion.get(ids=[f.id for f in fragmentos], include=["embeddings"])
        por_id = dict(zip(guardado["ids"], guardado["embeddings"]))
        self._vectores = np.array([por_id[f.id] for f in fragmentos], dtype=float)
        self._fragmentos = fragmentos
        self.documentos = documentos
        self._bm25 = BM25([f.texto for f in fragmentos])
        self._huella = nueva_huella
        return reconstruir

    @property
    def total_fragmentos(self) -> int:
        return len(self._fragmentos)

    # ----------------------------------------------------------------- buscar
    def buscar(
        self,
        consulta: str,
        categorias: list[str] | None = None,
        max_resultados: int = 5,
    ) -> list[Resultado]:
        import numpy as np

        consulta = (consulta or "").strip()
        if not consulta:
            return []
        self.preparar()

        candidatos = [
            i
            for i, f in enumerate(self._fragmentos)
            if not categorias or f.metadatos.get("categoria") in categorias
        ]
        if not candidatos:
            return []

        q = np.array(self.embedder.consulta(consulta), dtype=float)
        similitudes = self._vectores[candidatos] @ q
        lexicos_todos = self._bm25.puntajes(consulta)
        lexicos = [lexicos_todos[i] for i in candidatos]

        rrf = [0.0] * len(candidatos)
        for rank, pos in enumerate(np.argsort(-similitudes)):
            rrf[pos] += 1 / (RRF_K + rank + 1)
        orden_lex = sorted(range(len(candidatos)), key=lambda p: -lexicos[p])
        for rank, pos in enumerate(orden_lex):
            if lexicos[pos] > 0:
                rrf[pos] += 1 / (RRF_K + rank + 1)

        mejores = sorted(range(len(candidatos)), key=lambda p: -rrf[p])[:max_resultados]
        return [
            Resultado(
                fragmento=self._fragmentos[candidatos[p]],
                puntaje=rrf[p],
                similitud=float(similitudes[p]),
                puntaje_lexico=lexicos[p],
            )
            for p in mejores
        ]
