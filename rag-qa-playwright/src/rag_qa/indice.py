"""Índice del RAG: guarda los vectores en Chroma y hace la búsqueda híbrida.

Búsqueda híbrida = búsqueda por significado (vectores) + búsqueda por palabras
clave (BM25), combinadas con Reciprocal Rank Fusion (RRF). La búsqueda por
palabras clave se hace dos veces: sobre el texto completo de cada sección y solo
sobre su título, para que una sección corta con un título preciso ("C4. Nombres
de tests") no pierda frente a secciones largas que repiten mucho una palabra.
Así funciona bien
tanto con preguntas en lenguaje natural ("¿cómo nombro un page object?") como
con mensajes de error exactos ("strict mode violation").

El índice se reconstruye solo cuando cambia algún documento de knowledge-base/.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

from .config import Config
from .documentos import (
    AYUDA_FORMATO,
    Documento,
    ErrorDocumento,
    Fragmento,
    cargar_documentos,
    fragmentar_todo,
    huella,
)
from .embeddings import Embedder, crear_embedder
from .lexico import BM25

# Chroma no envía estadísticas de uso a internet.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

NOMBRE_COLECCION = "knowledge_base"

# Amortigua la ventaja de los primeros puestos en la fusión RRF (valor estándar).
CONSTANTE_FUSION = 60

# Cuánto pesa cada ranking en la fusión. El ranking por título pesa menos: ayuda
# a desempatar preguntas en lenguaje natural sin tapar los mensajes de error exactos.
PESO_SIGNIFICADO = 1.0
PESO_PALABRAS = 1.0
PESO_TITULO = 0.7

# En la búsqueda general (sin filtrar por categoría) estas categorías pesan menos:
# son código de la plantilla e instrucciones para el asistente, y no deben ganarles
# a las reglas, convenciones y errores en preguntas conceptuales. No se excluyen:
# si son lo único que responde, igual aparecen.
PESO_CATEGORIA_EN_BUSQUEDA_GENERAL = {"plantilla": 0.8, "comportamiento": 0.8}


@dataclass
class Resultado:
    fragmento: Fragmento
    puntaje: float          # puntaje combinado (más alto = más relevante)
    similitud: float        # similitud por vectores (-1 a 1)
    puntaje_lexico: float   # puntaje BM25 (0 = ninguna palabra en común)


class Indice:
    """Guarda los fragmentos en Chroma y busca combinando significado y palabras clave."""

    def __init__(self, config: Config | None = None, embedder: Embedder | None = None):
        self.config = config or Config()
        self.embedder = embedder or crear_embedder(self.config.embedder, self.config.modelo)
        self.documentos: list[Documento] = []
        self._fragmentos: list[Fragmento] = []
        self._vectores = None
        self._bm25: BM25 | None = None          # palabras clave sobre el texto completo
        self._bm25_titulos: BM25 | None = None  # palabras clave solo sobre los títulos
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

        # 1. ¿Cambió algo desde la última vez?
        documentos = cargar_documentos(self.config.kb_dir)
        nueva_huella = huella(documentos, self.embedder.nombre)
        if not forzar and nueva_huella == self._huella:
            return False

        # 2. Reconstruir la colección de Chroma si hace falta.
        fragmentos = fragmentar_todo(documentos)
        if not fragmentos:
            # Chroma no acepta una colección vacía y su error no se entiende.
            raise ErrorDocumento("ningún documento tiene secciones '## ' con contenido. " + AYUDA_FORMATO)
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

        # 3. Cargar los vectores en memoria para buscar rápido.
        guardado = coleccion.get(ids=[f.id for f in fragmentos], include=["embeddings"])
        vector_por_id = dict(zip(guardado["ids"], guardado["embeddings"]))
        faltantes = [f.id for f in fragmentos if f.id not in vector_por_id]
        if faltantes:
            raise RuntimeError(
                f"El índice está incompleto (faltan {len(faltantes)} secciones). "
                "Ejecuta: rag-qa indexar"
            )
        self._vectores = np.array([vector_por_id[f.id] for f in fragmentos], dtype=float)
        self._fragmentos = fragmentos
        self.documentos = documentos
        self._bm25 = BM25([f.texto for f in fragmentos])
        self._bm25_titulos = BM25([titulo_completo(f) for f in fragmentos])
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

        vector_consulta = np.array(self.embedder.consulta(consulta), dtype=float)
        similitudes = self._vectores[candidatos] @ vector_consulta
        lexicos_todos = self._bm25.puntajes(consulta)
        lexicos = [lexicos_todos[i] for i in candidatos]
        titulos_todos = self._bm25_titulos.puntajes(consulta)
        lexicos_titulo = [titulos_todos[i] for i in candidatos]

        # Fusión por puestos (RRF): cada fragmento suma peso/(CONSTANTE_FUSION + puesto)
        # en cada ranking (significado, palabras del texto y palabras del título).
        # Gana el que aparece arriba en varios, sin comparar puntajes de escalas
        # distintas. Si no comparte ninguna palabra, no suma en los rankings por palabras.
        puntaje_combinado = [0.0] * len(candidatos)
        _sumar_puestos(puntaje_combinado, list(similitudes), PESO_SIGNIFICADO, solo_positivos=False)
        _sumar_puestos(puntaje_combinado, lexicos, PESO_PALABRAS, solo_positivos=True)
        _sumar_puestos(puntaje_combinado, lexicos_titulo, PESO_TITULO, solo_positivos=True)
        if not categorias:
            for posicion, indice_fragmento in enumerate(candidatos):
                categoria = self._fragmentos[indice_fragmento].metadatos.get("categoria")
                puntaje_combinado[posicion] *= PESO_CATEGORIA_EN_BUSQUEDA_GENERAL.get(categoria, 1.0)

        mejores = sorted(
            range(len(candidatos)), key=lambda posicion: -puntaje_combinado[posicion]
        )[:max_resultados]
        return [
            Resultado(
                fragmento=self._fragmentos[candidatos[posicion]],
                puntaje=puntaje_combinado[posicion],
                similitud=float(similitudes[posicion]),
                puntaje_lexico=lexicos[posicion],
            )
            for posicion in mejores
        ]


def titulo_completo(fragmento: Fragmento) -> str:
    """Título del documento + título de la sección, por ejemplo
    "Convenciones del equipo — C4. Nombres de tests"."""
    return f"{fragmento.metadatos.get('titulo_doc', '')} — {fragmento.seccion}"


def _sumar_puestos(
    puntaje_combinado: list[float], puntajes: list[float], peso: float, solo_positivos: bool
):
    """Suma a cada fragmento peso/(CONSTANTE_FUSION + puesto) según su puesto en `puntajes`."""
    orden = sorted(range(len(puntajes)), key=lambda posicion: -puntajes[posicion])
    for puesto, posicion in enumerate(orden, start=1):
        if solo_positivos and puntajes[posicion] <= 0:
            continue
        puntaje_combinado[posicion] += peso / (CONSTANTE_FUSION + puesto)
