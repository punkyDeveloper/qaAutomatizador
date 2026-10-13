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

from .herramientas import CATEGORIAS, Herramientas
from .indice import Indice

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
    h = herramientas or Herramientas(Indice())
    servidor = MCPServer(name="rag-qa-playwright", instructions=INSTRUCCIONES, version="1.0.0")

    @servidor.tool(
        title="Revisar código de pruebas",
        description=(
            "Revisa una prueba de Playwright o un Page Object contra las reglas y convenciones "
            "del equipo. Devuelve el formato de respuesta, los checklists y las reglas relacionadas. "
            "Úsala cuando el usuario pida revisar, validar o mejorar código de pruebas."
        ),
    )
    def revisar_codigo(
        codigo: Annotated[str, Field(description="Código completo a revisar.")],
        archivo: Annotated[str | None, Field(description="Ruta del archivo, si se conoce.")] = None,
    ) -> str:
        return h.revisar_codigo(codigo, archivo)

    @servidor.tool(
        title="Diagnosticar error de Playwright",
        description=(
            "Busca un error de consola de Playwright en el catálogo del equipo y devuelve la causa, "
            "la solución y cómo ubicar el archivo y la línea. Úsala cuando una prueba falle "
            "o el usuario pegue un error."
        ),
    )
    def diagnosticar_error(
        error: Annotated[str, Field(description="Error completo de la consola, con el stack trace.")],
        codigo_relacionado: Annotated[
            str | None, Field(description="Código del archivo y línea donde falló, si se tiene.")
        ] = None,
    ) -> str:
        return h.diagnosticar_error(error, codigo_relacionado)

    @servidor.tool(
        title="Plantilla de proyecto desde cero",
        description=(
            "Devuelve la plantilla oficial del equipo para crear un proyecto de pruebas "
            "Playwright + POM desde cero (carpetas, configuración y ejemplos con comentarios guía). "
            "Úsala solo cuando el proyecto es nuevo."
        ),
    )
    def plantilla_proyecto() -> str:
        return h.plantilla_proyecto()

    @servidor.tool(
        title="Buscar en la base de conocimiento",
        description=(
            "Busca en las reglas, convenciones, ejemplos y errores del equipo. "
            f"Categorías opcionales: {', '.join(CATEGORIAS)}."
        ),
    )
    def buscar_conocimiento(
        consulta: Annotated[str, Field(description="Pregunta o texto a buscar.")],
        categoria: Annotated[str | None, Field(description="Filtrar por una categoría.")] = None,
        max_resultados: Annotated[int, Field(ge=1, le=10, description="Cuántas secciones devolver.")] = 5,
    ) -> str:
        return h.buscar_conocimiento(consulta, categoria, max_resultados)

    @servidor.tool(
        title="Estado del RAG",
        description="Muestra cuántos documentos y secciones hay indexados y qué modelo se usa.",
    )
    def estado() -> str:
        return h.estado()

    @servidor.tool(
        title="Reindexar base de conocimiento",
        description=(
            "Reconstruye el índice desde cero. Normalmente no hace falta: el índice se "
            "actualiza solo cuando cambian los documentos."
        ),
    )
    def reindexar() -> str:
        return h.reindexar()

    return servidor


def main() -> None:
    servidor = crear_servidor()
    print("[rag-qa] Servidor MCP iniciado (stdio).", file=sys.stderr)
    servidor.run("stdio")


if __name__ == "__main__":
    main()
