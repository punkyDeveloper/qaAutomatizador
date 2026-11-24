"""Servidor MCP: expone las herramientas del RAG a GitHub Copilot (modo Agent).

VS Code lo inicia solo, según .vscode/mcp.json. Para probarlo a mano:
    python -m rag_qa.servidor_mcp

IMPORTANTE: el servidor se comunica con Copilot por la salida estándar (stdout).
Nada en este proceso debe imprimir en stdout; los mensajes van a stderr.
"""

from __future__ import annotations

import sys
from typing import Annotated

from pydantic import Field

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from .herramientas import CATEGORIAS, MAX_RESULTADOS_PERMITIDOS, Herramientas
from .indice import Indice

# Seguridad: tamaño máximo que acepta cada parámetro. Si se pasa, el protocolo
# MCP rechaza la llamada antes de ejecutar nada (evita llenar la memoria o
# dejar el servidor ocupado con textos gigantes).
MAX_CARACTERES_CODIGO = 200_000      # un archivo de pruebas grande cabe de sobra
MAX_CARACTERES_ERROR = 200_000       # un error con stack trace y call log largo
MAX_CARACTERES_CONSULTA = 20_000
MAX_CARACTERES_RUTA = 500
MAX_CARACTERES_CATEGORIA = 50

# Pistas para Copilot/Claude: estas herramientas solo leen y no salen a internet.
SOLO_LECTURA = ToolAnnotations(read_only_hint=True, open_world_hint=False)
# reindexar escribe la base vectorial local, pero no borra nada del usuario.
REINDEXA = ToolAnnotations(
    read_only_hint=False, destructive_hint=False, idempotent_hint=True, open_world_hint=False
)

INSTRUCCIONES = """\
Base de conocimiento del equipo de QA para pruebas de front con Playwright + Page Object Model en JavaScript.
Úsala SIEMPRE antes de responder sobre pruebas de Playwright:
- Revisar o validar código de pruebas o Page Objects -> revisar_codigo
- Un error de consola o una prueba que falla -> diagnosticar_error
- Crear un proyecto de pruebas desde cero -> plantilla_proyecto
- Cualquier otra duda (reglas, convenciones, ejemplos) -> buscar_conocimiento
En proyectos existentes solo se sugiere: no modifiques archivos.
"""


def crear_servidor(herramientas: Herramientas | None = None) -> MCPServer:
    herramientas_rag = herramientas or Herramientas(Indice())
    servidor = MCPServer(name="rag-qa-playwright", instructions=INSTRUCCIONES, version="1.0.0")

    @servidor.tool(
        title="Revisar código de pruebas",
        description=(
            "Revisa una prueba de Playwright o un Page Object contra las reglas y convenciones "
            "del equipo. Devuelve el formato de respuesta, los checklists y las reglas relacionadas. "
            "Úsala cuando el usuario pida revisar, validar o mejorar código de pruebas."
        ),
        annotations=SOLO_LECTURA,
    )
    def revisar_codigo(
        codigo: Annotated[
            str, Field(max_length=MAX_CARACTERES_CODIGO, description="Código completo a revisar.")
        ],
        archivo: Annotated[
            str | None,
            Field(max_length=MAX_CARACTERES_RUTA, description="Ruta del archivo, si se conoce."),
        ] = None,
    ) -> str:
        return herramientas_rag.revisar_codigo(codigo, archivo)

    @servidor.tool(
        title="Diagnosticar error de Playwright",
        description=(
            "Busca un error de consola de Playwright en el catálogo del equipo y devuelve la causa, "
            "la solución y cómo ubicar el archivo y la línea. Úsala cuando una prueba falle "
            "o el usuario pegue un error."
        ),
        annotations=SOLO_LECTURA,
    )
    def diagnosticar_error(
        error: Annotated[
            str,
            Field(
                max_length=MAX_CARACTERES_ERROR,
                description="Error completo de la consola, con el stack trace.",
            ),
        ],
        codigo_relacionado: Annotated[
            str | None,
            Field(
                max_length=MAX_CARACTERES_CODIGO,
                description="Código del archivo y línea donde falló, si se tiene.",
            ),
        ] = None,
    ) -> str:
        return herramientas_rag.diagnosticar_error(error, codigo_relacionado)

    @servidor.tool(
        title="Plantilla de proyecto desde cero",
        description=(
            "Devuelve la plantilla oficial del equipo para crear un proyecto de pruebas "
            "Playwright + POM desde cero (carpetas, configuración y ejemplos con comentarios guía). "
            "Úsala solo cuando el proyecto es nuevo."
        ),
        annotations=SOLO_LECTURA,
    )
    def plantilla_proyecto() -> str:
        return herramientas_rag.plantilla_proyecto()

    @servidor.tool(
        title="Buscar en la base de conocimiento",
        description=(
            "Busca en las reglas, convenciones, ejemplos y errores del equipo. "
            f"Categorías opcionales: {', '.join(CATEGORIAS)}."
        ),
        annotations=SOLO_LECTURA,
    )
    def buscar_conocimiento(
        consulta: Annotated[
            str, Field(max_length=MAX_CARACTERES_CONSULTA, description="Pregunta o texto a buscar.")
        ],
        categoria: Annotated[
            str | None,
            Field(max_length=MAX_CARACTERES_CATEGORIA, description="Filtrar por una categoría."),
        ] = None,
        max_resultados: Annotated[
            int,
            Field(ge=1, le=MAX_RESULTADOS_PERMITIDOS, description="Cuántas secciones devolver."),
        ] = 5,
    ) -> str:
        return herramientas_rag.buscar_conocimiento(consulta, categoria, max_resultados)

    @servidor.tool(
        title="Estado del RAG",
        description="Muestra cuántos documentos y secciones hay indexados y qué modelo se usa.",
        annotations=SOLO_LECTURA,
    )
    def estado() -> str:
        return herramientas_rag.estado()

    @servidor.tool(
        title="Reindexar base de conocimiento",
        description=(
            "Reconstruye el índice desde cero. Normalmente no hace falta: el índice se "
            "actualiza solo cuando cambian los documentos."
        ),
        annotations=REINDEXA,
    )
    def reindexar() -> str:
        return herramientas_rag.reindexar()

    return servidor


def main() -> None:
    servidor = crear_servidor()
    print("[rag-qa] Servidor MCP iniciado (stdio).", file=sys.stderr)
    servidor.run("stdio")


if __name__ == "__main__":
    main()
