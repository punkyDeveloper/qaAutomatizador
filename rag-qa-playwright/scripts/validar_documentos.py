"""
Valida que todos los documentos de knowledge-base/ cumplan el estándar
definido en docs/estandar-documentos.md.

Uso (desde la raíz del proyecto):
    python scripts/validar_documentos.py

No necesita instalar nada: usa solo la librería estándar de Python.
"""

import re
import sys
from pathlib import Path

CARPETA = Path(__file__).resolve().parent.parent / "knowledge-base"

OBLIGATORIOS = ["id", "lenguaje", "framework", "tipo", "patron", "categoria", "version"]

VALORES_PERMITIDOS = {
    "lenguaje": {"javascript"},
    "framework": {"playwright"},
    "tipo": {"ui"},
    "patron": {"pom"},
    "categoria": {
        "buenas-practicas", "convenciones", "comportamiento",
        "ejemplos", "errores", "plantilla",
    },
}

# Una sección (##) más larga que esto puede dar malos resultados en la búsqueda.
MAX_CARACTERES_SECCION = 4000


def leer_metadatos(texto):
    """Devuelve (metadatos, cuerpo) o (None, texto) si no hay bloque ---."""
    if not texto.startswith("---\n"):
        return None, texto
    fin = texto.find("\n---\n", 4)
    if fin == -1:
        return None, texto
    metadatos = {}
    for linea in texto[4:fin].splitlines():
        if ":" in linea:
            clave, valor = linea.split(":", 1)
            metadatos[clave.strip()] = valor.strip().strip('"')
    return metadatos, texto[fin + 5:]


def validar(ruta, ids_vistos):
    errores, avisos = [], []
    texto = ruta.read_text(encoding="utf-8")
    metadatos, cuerpo = leer_metadatos(texto)

    if metadatos is None:
        return ["No tiene el bloque de metadatos entre líneas ---"], avisos

    for campo in OBLIGATORIOS:
        if not metadatos.get(campo):
            errores.append(f"Falta el campo obligatorio '{campo}'")

    for campo, permitidos in VALORES_PERMITIDOS.items():
        valor = metadatos.get(campo)
        if valor and valor not in permitidos:
            errores.append(f"'{campo}: {valor}' no es válido. Permitidos: {sorted(permitidos)}")

    doc_id = metadatos.get("id")
    if doc_id:
        if not re.fullmatch(r"(gen|js)-[a-z0-9-]+-\d{3}", doc_id):
            errores.append(f"El id '{doc_id}' no sigue el formato prefijo-tema-001")
        if doc_id in ids_vistos:
            errores.append(f"El id '{doc_id}' está repetido en {ids_vistos[doc_id]}")
        ids_vistos[doc_id] = ruta.name

    if not re.search(r"^# ", cuerpo, re.MULTILINE):
        errores.append("No tiene título principal (línea que empieza con '# ')")

    # Separar secciones ## ignorando lo que esté dentro de bloques de código
    secciones, actual, en_codigo = [], None, False
    for linea in cuerpo.splitlines():
        if linea.startswith("```"):
            en_codigo = not en_codigo
        if not en_codigo and linea.startswith("## "):
            actual = [linea[3:].strip(), ""]
            secciones.append(actual)
        elif actual:
            actual[1] += linea + "\n"

    if not secciones:
        errores.append("No tiene secciones '## '. El RAG las usa para dividir el documento")

    for titulo, contenido in secciones:
        largo = len(contenido.strip())
        if largo == 0:
            avisos.append(f"La sección '{titulo}' está vacía")
        elif largo > MAX_CARACTERES_SECCION:
            avisos.append(f"La sección '{titulo}' es muy larga ({largo} caracteres); considera dividirla")

    return errores, avisos


def main():
    archivos = sorted(CARPETA.rglob("*.md"))
    if not archivos:
        print(f"No se encontraron documentos en {CARPETA}")
        return 1

    ids_vistos, total_errores = {}, 0
    for ruta in archivos:
        errores, avisos = validar(ruta, ids_vistos)
        nombre = ruta.relative_to(CARPETA)
        if not errores and not avisos:
            print(f"✅ {nombre}")
            continue
        print(f"{'❌' if errores else '⚠️ '} {nombre}")
        for e in errores:
            print(f"     ERROR: {e}")
        for a in avisos:
            print(f"     AVISO: {a}")
        total_errores += len(errores)

    print(f"\n{len(archivos)} documentos revisados, {total_errores} errores.")
    return 1 if total_errores else 0


if __name__ == "__main__":
    sys.exit(main())
