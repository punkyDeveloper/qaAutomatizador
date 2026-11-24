"""Lectura de la base de conocimiento y división en fragmentos (chunks).

Cada documento .md se parte por sus secciones "## ". Cada sección es un
fragmento que el RAG puede encontrar por sí solo (ver docs/estandar-documentos.md).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

# Si cambia la forma de partir o indexar los documentos, se sube este número
# para que el índice se reconstruya solo.
# 2: la búsqueda también puntúa por el título de cada sección.
VERSION_FRAGMENTADOR = "2"

# La introducción (texto antes del primer "## ") solo se indexa si tiene contenido real.
MIN_CARACTERES_INTRO = 80

# Un documento más grande que esto no es normal: se ignora por seguridad.
MAX_BYTES_DOCUMENTO = 1_000_000

# Cómo arreglar un documento que no cumple el estándar.
AYUDA_FORMATO = (
    "Revisa el formato en docs/estandar-documentos.md "
    "o ejecuta: python scripts/validar_documentos.py"
)

# Marcas que abren y cierran el bloque de metadatos.
INICIO_METADATOS = "---\n"
FIN_METADATOS = "\n---\n"

# Marca invisible (BOM) que algunos editores de Windows agregan al inicio del archivo.
MARCA_BOM = "﻿"


@dataclass
class Documento:
    ruta: Path
    archivo: str                 # ruta relativa a knowledge-base, con "/"
    metadatos: dict[str, str]
    titulo: str
    cuerpo: str                  # todo lo que va después del bloque de metadatos
    # Bytes leídos del archivo: la huella usa estos mismos, sin volver a leer el disco.
    contenido_bytes: bytes = field(default=b"", repr=False)

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
    texto = texto.replace("\r\n", "\n").lstrip(MARCA_BOM)
    if not texto.startswith(INICIO_METADATOS):
        raise ErrorDocumento("no tiene bloque de metadatos entre líneas ---")
    # -1: con un bloque vacío (---\n---\n) el \n de la apertura también es parte del cierre.
    fin = texto.find(FIN_METADATOS, len(INICIO_METADATOS) - 1)
    if fin == -1:
        raise ErrorDocumento("el bloque de metadatos no está cerrado con ---")
    metadatos: dict[str, str] = {}
    for linea in texto[len(INICIO_METADATOS):fin].splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            metadatos[clave.strip()] = valor.strip().strip('"').strip("'")
    return metadatos, texto[fin + len(FIN_METADATOS):]


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
        # Si ya empezó una sección, la línea es parte de ella; si no, de la introducción.
        destino = secciones[-1][1] if secciones else intro
        destino.append(linea)

    def limpiar(lineas: list[str]) -> str:
        # Quita separadores "---" y líneas vacías sobrantes al inicio y al final.
        while lineas and lineas[-1].strip() in ("", "---"):
            lineas.pop()
        while lineas and lineas[0].strip() in ("", "---"):
            lineas.pop(0)
        return "\n".join(lineas)

    return titulo, limpiar(intro), [(s, limpiar(c)) for s, c in secciones]


def cargar_documento(ruta: Path, kb_dir: Path) -> Documento:
    """Lee un .md de la base. Si no cumple el estándar, el error dice qué archivo es."""
    datos = _leer_con_limite(ruta)
    try:
        texto = datos.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ErrorDocumento(f"{ruta.name}: no está guardado en UTF-8; guárdalo como UTF-8. {AYUDA_FORMATO}") from e
    # Igual que read_text: los saltos de línea de Windows o Mac antiguo pasan a "\n".
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")
    try:
        metadatos, cuerpo = leer_metadatos(texto)
    except ErrorDocumento as e:
        raise ErrorDocumento(f"{ruta.name}: {e}. {AYUDA_FORMATO}") from e
    titulo, _, _ = dividir_secciones(cuerpo)
    return Documento(
        ruta=ruta,
        archivo=ruta.relative_to(kb_dir).as_posix(),
        metadatos=metadatos,
        titulo=titulo or ruta.stem,
        cuerpo=cuerpo,
        contenido_bytes=datos,
    )


def _leer_con_limite(ruta: Path) -> bytes:
    """Lee como mucho MAX_BYTES_DOCUMENTO + 1 bytes.

    Seguridad: el archivo pudo crecer después de revisar su tamaño, así que
    nunca se lee completo a ciegas; si pasa el límite, se rechaza.
    """
    with ruta.open("rb") as archivo:
        datos = archivo.read(MAX_BYTES_DOCUMENTO + 1)
    if len(datos) > MAX_BYTES_DOCUMENTO:
        raise ErrorDocumento(f"{ruta.name}: pesa más de {MAX_BYTES_DOCUMENTO} bytes. {AYUDA_FORMATO}")
    return datos


def _es_documento_seguro(ruta: Path, kb_dir: Path) -> bool:
    """Descarta enlaces simbólicos, enlaces duros, archivos fuera de la base y archivos enormes."""
    if ruta.is_symlink() or not ruta.resolve().is_relative_to(kb_dir.resolve()):
        return False
    informacion = ruta.stat()
    # st_nlink > 1: es un enlace duro, el mismo archivo puede estar fuera de la base.
    return informacion.st_nlink == 1 and informacion.st_size <= MAX_BYTES_DOCUMENTO


def cargar_documentos(kb_dir: Path) -> list[Documento]:
    """Lee todos los .md de la base de conocimiento (solo los seguros, ver arriba)."""
    if not kb_dir.is_dir():
        raise FileNotFoundError(
            f"No existe la carpeta de conocimiento: {kb_dir}. "
            "Revisa la variable de entorno RAG_QA_KB o crea la carpeta knowledge-base/."
        )
    rutas = [r for r in sorted(kb_dir.rglob("*.md")) if _es_documento_seguro(r, kb_dir)]
    documentos = [cargar_documento(r, kb_dir) for r in rutas]
    if not documentos:
        raise FileNotFoundError(
            f"No hay documentos .md en {kb_dir}. "
            "Agrega uno a partir de docs/plantilla-nuevo-documento.md."
        )
    archivo_por_id: dict[str, str] = {}
    for doc in documentos:
        if doc.id in archivo_por_id:
            raise ErrorDocumento(
                f"id repetido '{doc.id}' en {doc.archivo} y {archivo_por_id[doc.id]}. "
                "Cambia el id de uno de los dos."
            )
        archivo_por_id[doc.id] = doc.archivo
    return documentos


def fragmentar(documento: Documento) -> list[Fragmento]:
    """Parte un documento en un fragmento por sección "## " (y la introducción si tiene contenido)."""
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
    for orden, (seccion, contenido) in enumerate(partes):
        fragmentos.append(
            Fragmento(
                id=f"{documento.id}#{orden:02d}",
                texto=f"{documento.titulo} — {seccion}\n\n{contenido}",
                seccion=seccion,
                contenido=contenido,
                metadatos={**base, "seccion": seccion, "orden": str(orden)},
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
    calculadora = hashlib.sha256(f"{VERSION_FRAGMENTADOR}|{extra}".encode())
    for doc in sorted(documentos, key=lambda d: d.archivo):
        calculadora.update(doc.archivo.encode())
        calculadora.update(doc.contenido_bytes.replace(b"\r\n", b"\n"))
    return calculadora.hexdigest()
