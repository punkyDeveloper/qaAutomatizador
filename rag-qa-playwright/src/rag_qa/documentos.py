"""Lectura de la base de conocimiento y división en fragmentos (chunks).

Cada documento .md se parte por sus secciones "## ". Cada sección es un
fragmento que el RAG puede encontrar por sí solo (ver docs/estandar-documentos.md).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

# Si cambia la forma de partir los documentos, se sube este número
# para que el índice se reconstruya solo.
VERSION_FRAGMENTADOR = "1"

# La introducción (texto antes del primer "## ") solo se indexa si tiene contenido real.
MIN_CARACTERES_INTRO = 80


@dataclass
class Documento:
    ruta: Path
    archivo: str                 # ruta relativa a knowledge-base, con "/"
    metadatos: dict[str, str]
    titulo: str
    cuerpo: str                  # todo lo que va después del bloque de metadatos

    @property
    def id(self) -> str:
        return self.metadatos.get("id", self.archivo)

    @property
    def categoria(self) -> str:
        return self.metadatos.get("categoria", "")


@dataclass
class Fragmento:
    id: str
    texto: str                   # lo que se indexa (incluye título y sección)
    seccion: str
    contenido: str               # solo el contenido de la sección
    metadatos: dict[str, str] = field(default_factory=dict)


class ErrorDocumento(ValueError):
    """El documento no cumple el estándar mínimo para indexarse."""


def leer_metadatos(texto: str) -> tuple[dict[str, str], str]:
    """Separa el bloque --- inicial del resto. Devuelve (metadatos, cuerpo)."""
    texto = texto.replace("\r\n", "\n").lstrip("﻿")
    if not texto.startswith("---\n"):
        raise ErrorDocumento("no tiene bloque de metadatos entre líneas ---")
    fin = texto.find("\n---\n", 4)
    if fin == -1:
        raise ErrorDocumento("el bloque de metadatos no está cerrado con ---")
    metadatos: dict[str, str] = {}
    for linea in texto[4:fin].splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            metadatos[clave.strip()] = valor.strip().strip('"').strip("'")
    return metadatos, texto[fin + 5:]


def dividir_secciones(cuerpo: str) -> tuple[str, str, list[tuple[str, str]]]:
    """Divide el cuerpo en (título, introducción, [(sección, contenido), ...]).

    Los "#" que estén dentro de bloques de código ``` no cuentan como títulos.
    """
    titulo = ""
    intro: list[str] = []
    secciones: list[list] = []
    en_codigo = False
    for linea in cuerpo.splitlines():
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        if not en_codigo and linea.startswith("# ") and not titulo:
            titulo = linea[2:].strip()
            continue
        if not en_codigo and linea.startswith("## "):
            secciones.append([linea[3:].strip(), []])
            continue
        (secciones[-1][1] if secciones else intro).append(linea)

    def limpiar(lineas: list[str]) -> str:
        # Quita separadores "---" y líneas vacías sobrantes al inicio y al final.
        while lineas and lineas[-1].strip() in ("", "---"):
            lineas.pop()
        while lineas and lineas[0].strip() in ("", "---"):
            lineas.pop(0)
        return "\n".join(lineas)

    return titulo, limpiar(intro), [(s, limpiar(c)) for s, c in secciones]


def cargar_documento(ruta: Path, kb_dir: Path) -> Documento:
    texto = ruta.read_text(encoding="utf-8")
    metadatos, cuerpo = leer_metadatos(texto)
    titulo, _, _ = dividir_secciones(cuerpo)
    return Documento(
        ruta=ruta,
        archivo=ruta.relative_to(kb_dir).as_posix(),
        metadatos=metadatos,
        titulo=titulo or ruta.stem,
        cuerpo=cuerpo,
    )


def cargar_documentos(kb_dir: Path) -> list[Documento]:
    if not kb_dir.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de conocimiento: {kb_dir}")
    documentos = [cargar_documento(r, kb_dir) for r in sorted(kb_dir.rglob("*.md"))]
    if not documentos:
        raise FileNotFoundError(f"No hay documentos .md en {kb_dir}")
    vistos: dict[str, str] = {}
    for doc in documentos:
        if doc.id in vistos:
            raise ErrorDocumento(f"id repetido '{doc.id}' en {doc.archivo} y {vistos[doc.id]}")
        vistos[doc.id] = doc.archivo
    return documentos


def fragmentar(documento: Documento) -> list[Fragmento]:
    titulo, intro, secciones = dividir_secciones(documento.cuerpo)
    partes: list[tuple[str, str]] = []
    if len(intro) >= MIN_CARACTERES_INTRO:
        partes.append(("Introducción", intro))
    partes.extend((s, c) for s, c in secciones if c.strip())

    base = {
        "doc_id": documento.id,
        "archivo": documento.archivo,
        "titulo_doc": documento.titulo,
        "categoria": documento.categoria,
        "lenguaje": documento.metadatos.get("lenguaje", ""),
        "version_doc": documento.metadatos.get("version", ""),
    }
    fragmentos = []
    for i, (seccion, contenido) in enumerate(partes):
        fragmentos.append(
            Fragmento(
                id=f"{documento.id}#{i:02d}",
                texto=f"{documento.titulo} — {seccion}\n\n{contenido}",
                seccion=seccion,
                contenido=contenido,
                metadatos={**base, "seccion": seccion, "orden": str(i)},
            )
        )
    return fragmentos


def fragmentar_todo(documentos: list[Documento]) -> list[Fragmento]:
    return [f for doc in documentos for f in fragmentar(doc)]


def huella(documentos: list[Documento], extra: str = "") -> str:
    """Hash del contenido de la base de conocimiento.

    Si cambia cualquier documento (o el modelo, que va en `extra`),
    la huella cambia y el índice se reconstruye automáticamente.
    """
    h = hashlib.sha256(f"{VERSION_FRAGMENTADOR}|{extra}".encode())
    for doc in sorted(documentos, key=lambda d: d.archivo):
        h.update(doc.archivo.encode())
        h.update(doc.ruta.read_bytes().replace(b"\r\n", b"\n"))
    return h.hexdigest()


def buscar_seccion(documentos: list[Documento], doc_id: str, inicio_seccion: str) -> str:
    """Devuelve el contenido de una sección por id de documento y comienzo del título."""
    for doc in documentos:
        if doc.id != doc_id:
            continue
        for frag in fragmentar(doc):
            if frag.seccion.lower().startswith(inicio_seccion.lower()):
                return frag.contenido
    return ""


def documento_por_categoria(documentos: list[Documento], categoria: str) -> list[Documento]:
    return [d for d in documentos if d.categoria == categoria]
