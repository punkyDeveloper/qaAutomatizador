"""Comandos de consola del RAG.

    rag-qa indexar                 Construye (o reconstruye) el índice.
    rag-qa buscar "texto"          Busca en la base de conocimiento.
    rag-qa buscar "texto" -c errores
    rag-qa error "texto del error" Simula la herramienta diagnosticar_error.
    rag-qa estado                  Muestra documentos y secciones indexadas.
"""

from __future__ import annotations

import argparse
import sys

from .documentos import ErrorDocumento
from .herramientas import CATEGORIAS, MAX_RESULTADOS_PERMITIDOS, Herramientas
from .indice import Indice


def _crear_parser() -> argparse.ArgumentParser:
    """Define los comandos y sus opciones."""
    parser = argparse.ArgumentParser(prog="rag-qa", description="RAG de calidad de software")
    subcomandos = parser.add_subparsers(dest="comando", required=True)
    subcomandos.add_parser("indexar", help="Reconstruye el índice")
    comando_buscar = subcomandos.add_parser("buscar", help="Busca en la base de conocimiento")
    comando_buscar.add_argument("consulta")
    comando_buscar.add_argument("-c", "--categoria", choices=CATEGORIAS)
    comando_buscar.add_argument("-n", "--max", type=int, default=5)
    comando_error = subcomandos.add_parser("error", help="Diagnostica un error de consola")
    comando_error.add_argument("error")
    subcomandos.add_parser("estado", help="Muestra el estado del índice")
    return parser


def _ejecutar(args: argparse.Namespace) -> None:
    """Ejecuta el comando elegido e imprime el resultado."""
    indice = Indice()
    herramientas = Herramientas(indice)
    if args.comando == "indexar":
        print(herramientas.reindexar())
    elif args.comando == "buscar":
        # Entre 1 y el máximo permitido (un número negativo daría resultados raros).
        max_resultados = max(1, min(args.max, MAX_RESULTADOS_PERMITIDOS))
        resultados = indice.buscar(
            args.consulta, [args.categoria] if args.categoria else None, max_resultados
        )
        if not resultados:
            print("Sin resultados.")
        for numero, resultado in enumerate(resultados, 1):
            metadatos = resultado.fragmento.metadatos
            print(f"{numero}. [{metadatos['categoria']}] {metadatos['archivo']} › {metadatos['seccion']}")
            print(
                f"   similitud={resultado.similitud:.3f}  "
                f"palabras_clave={resultado.puntaje_lexico:.2f}"
            )
    elif args.comando == "error":
        print(herramientas.diagnosticar_error(args.error))
    elif args.comando == "estado":
        print(herramientas.estado())


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # tildes y emojis en la consola de Windows
        except Exception:
            pass

    args = _crear_parser().parse_args(argv)
    try:
        _ejecutar(args)
    except (FileNotFoundError, ErrorDocumento) as error:
        # Un documento mal escrito o una carpeta que falta: mensaje claro, sin traceback.
        print(f"ERROR: {error}", file=sys.stderr)
        print("Revisa los documentos con: python scripts/validar_documentos.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
