"""Pruebas del servidor MCP: lo que Copilot ve y usa (Paso 6).

- En proceso: rápido, valida herramientas y respuestas.
- Por stdio: arranca el servidor como lo hace VS Code (subproceso) y le habla
  por el protocolo MCP real.
"""

import asyncio
import os
import sys

from mcp import Client, StdioServerParameters

from rag_qa.servidor_mcp import crear_servidor

HERRAMIENTAS_ESPERADAS = {
    "revisar_codigo",
    "diagnosticar_error",
    "plantilla_proyecto",
    "buscar_conocimiento",
    "estado",
    "reindexar",
}


def _texto(resultado) -> str:
    assert not resultado.is_error, resultado
    return resultado.content[0].text


def test_servidor_expone_todas_las_herramientas(herramientas):
    async def ejecutar():
        async with Client(crear_servidor(herramientas)) as c:
            return await c.list_tools()

    herramientas_mcp = asyncio.run(ejecutar()).tools
    assert {t.name for t in herramientas_mcp} == HERRAMIENTAS_ESPERADAS
    for t in herramientas_mcp:
        assert t.description, f"{t.name} no tiene descripción (Copilot la usa para decidir)"


def test_servidor_tiene_instrucciones_para_copilot(herramientas):
    servidor = crear_servidor(herramientas)
    assert "diagnosticar_error" in servidor.instructions
    assert "no modifiques archivos" in servidor.instructions


def test_llamar_herramientas_por_mcp(herramientas):
    async def ejecutar():
        async with Client(crear_servidor(herramientas)) as c:
            return (
                await c.call_tool("diagnosticar_error", {"error": "strict mode violation resolved to 2 elements"}),
                await c.call_tool("revisar_codigo", {"codigo": "await page.waitForTimeout(3000);"}),
                await c.call_tool("plantilla_proyecto", {}),
                await c.call_tool("buscar_conocimiento", {"consulta": "storageState", "max_resultados": 2}),
            )

    error, revision, plantilla, busqueda = (_texto(r) for r in asyncio.run(ejecutar()))
    assert "Strict mode violation" in error
    assert "Regla 3" in revision
    assert "playwright.config.js" in plantilla
    assert "storageState" in busqueda


def test_parametro_invalido_devuelve_error(herramientas):
    async def ejecutar():
        async with Client(crear_servidor(herramientas)) as c:
            return await c.call_tool("buscar_conocimiento", {"consulta": "x", "max_resultados": 99})

    assert asyncio.run(ejecutar()).is_error


def test_servidor_real_por_stdio(tmp_path):
    """Arranca `python -m rag_qa.servidor_mcp` como lo haría VS Code."""
    entorno = {**os.environ, "RAG_QA_EMBEDDER": "hash", "RAG_QA_DB": str(tmp_path / "db")}
    parametros = StdioServerParameters(
        command=sys.executable, args=["-m", "rag_qa.servidor_mcp"], env=entorno
    )

    async def ejecutar():
        async with Client(parametros, read_timeout_seconds=120) as c:
            tools = await c.list_tools()
            r = await c.call_tool("diagnosticar_error", {"error": "Error: No tests found"})
            return tools, r

    tools, resultado = asyncio.run(ejecutar())
    assert {t.name for t in tools.tools} == HERRAMIENTAS_ESPERADAS
    assert "Error: No tests found" in _texto(resultado)
