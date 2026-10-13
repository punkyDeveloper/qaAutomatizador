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

from .herramientas import CATEGORIAS, Herramientas
from .indice import Indice


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")  # tildes y emojis en la consola de Windows
        except Exception:
            pass

    parser = argparse.ArgumentParser(prog="rag-qa", description="RAG de calidad de software")
    sub = parser.add_subparsers(dest="comando", required=True)
    sub.add_parser("indexar", help="Reconstruye el índice")
    p_buscar = sub.add_parser("buscar", help="Busca en la base de conocimiento")
    p_buscar.add_argument("consulta")
    p_buscar.add_argument("-c", "--categoria", choices=CATEGORIAS)
    p_buscar.add_argument("-n", "--max", type=int, default=5)
    p_error = sub.add_parser("error", help="Diagnostica un error de consola")
    p_error.add_argument("error")
    sub.add_parser("estado", help="Muestra el estado del índice")
    args = parser.parse_args(argv)

    indice = Indice()
    h = Herramientas(indice)
    if args.comando == "indexar":
        print(h.reindexar())
    elif args.comando == "buscar":
        resultados = indice.buscar(
            args.consulta, [args.categoria] if args.categoria else None, args.max
        )
        if not resultados:
            print("Sin resultados.")
        for i, r in enumerate(resultados, 1):
            m = r.fragmento.metadatos
            print(f"{i}. [{m['categoria']}] {m['archivo']} › {m['seccion']}")
            print(f"   similitud={r.similitud:.3f}  palabras_clave={r.puntaje_lexico:.2f}")
    elif args.comando == "error":
        print(h.diagnosticar_error(args.error))
    elif args.comando == "estado":
        print(h.estado())
    return 0


if __name__ == "__main__":
    sys.exit(main())
