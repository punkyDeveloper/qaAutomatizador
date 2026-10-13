"""Pasos finales de la instalación (los ejecuta instalar.bat).

1. Indexa la base de conocimiento con el modelo real (la primera vez lo descarga).
2. Hace una consulta de prueba.
3. Configura Copilot: escribe .vscode/mcp.json en la carpeta del espacio de trabajo
   (la carpeta que contiene a rag-qa-playwright, por ejemplo qaAutomatizador).
4. Ejecuta todas las pruebas unitarias y de calidad.

Uso manual:  python -m rag_qa.instalar [--sin-pruebas]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .config import RAIZ_PROYECTO
from .herramientas import Herramientas
from .indice import Indice

NOMBRE_SERVIDOR = "rag-qa-playwright"


def configuracion_servidor() -> dict:
    return {
        "type": "stdio",
        "command": sys.executable,
        "args": ["-m", "rag_qa.servidor_mcp"],
    }


def escribir_mcp_json(carpeta_workspace: Path) -> Path:
    """Crea o actualiza .vscode/mcp.json sin borrar otros servidores que ya existan."""
    ruta = carpeta_workspace / ".vscode" / "mcp.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos: dict = {}
    if ruta.exists():
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            respaldo = ruta.with_suffix(".json.bak")
            ruta.replace(respaldo)
            print(f"   Aviso: mcp.json no era JSON válido; se guardó una copia en {respaldo.name}")
    datos.setdefault("servers", {})[NOMBRE_SERVIDOR] = configuracion_servidor()
    ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ruta


def main(argv: list[str] | None = None) -> int:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8")
        except Exception:
            pass
    argv = sys.argv[1:] if argv is None else argv

    print("\n-> Indexando la base de conocimiento con el modelo real.")
    print("   La primera vez descarga el modelo (~470 MB); puede tardar unos minutos.")
    herramientas = Herramientas(Indice())
    try:
        print("   " + herramientas.reindexar())
    except Exception as e:
        print(f"\nERROR al indexar: {type(e).__name__}: {e}")
        print("Si el error es de descarga, revisa tu conexión a internet y vuelve a ejecutar instalar.bat.")
        return 1

    print("\n-> Consulta de prueba: 'Error: locator.click: Timeout 30000ms exceeded'")
    resultado = herramientas.indice.buscar("Error: locator.click: Timeout 30000ms exceeded", max_resultados=1)
    print(f"   Encontró: {resultado[0].fragmento.metadatos['seccion']}")

    workspace = RAIZ_PROYECTO.parent
    ruta = escribir_mcp_json(workspace)
    print(f"\n-> Copilot configurado en: {ruta}")

    if "--sin-pruebas" not in argv:
        print("\n-> Ejecutando pruebas unitarias y de calidad...\n")
        codigo = subprocess.call(
            [sys.executable, "-m", "pytest", str(RAIZ_PROYECTO / "tests"), "-q", "-rs"],
            cwd=RAIZ_PROYECTO,
        )
        if codigo != 0:
            print("\nAlgunas pruebas fallaron. Copia el resultado de arriba y compártelo para revisarlo.")
            return codigo

    print(
        "\n============================================================\n"
        " RAG instalado y verificado.\n"
        "============================================================\n"
        f" 1. Abre en VS Code la carpeta: {workspace}\n"
        " 2. Abre el archivo .vscode/mcp.json y haz clic en 'Start' sobre\n"
        f"    el servidor '{NOMBRE_SERVIDOR}' (o acepta el aviso de confianza).\n"
        " 3. Abre el chat de Copilot, cambia a modo 'Agent' y revisa en el\n"
        "    ícono de herramientas que aparezca 'rag-qa-playwright'.\n"
        " 4. Prueba: pega un error de Playwright y pide que lo diagnostique.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
