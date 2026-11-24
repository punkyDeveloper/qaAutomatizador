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
import os
import subprocess
import sys
import time
from pathlib import Path

from .config import RAIZ_PROYECTO
from .herramientas import Herramientas
from .indice import Indice

NOMBRE_SERVIDOR = "rag-qa-playwright"


def ruta_python_para_vscode(python: Path | None = None, carpeta_usuario: Path | None = None) -> str:
    """Ruta del Python del RAG tal como se escribe en mcp.json.

    Si está dentro de la carpeta del usuario se escribe con ${userHome} (VS Code
    la reemplaza), para no guardar el nombre del usuario en un archivo que va a git
    y para que sirva en otro computador. Si no, se usa la ruta absoluta.
    """
    python = Path(sys.executable if python is None else python).absolute()
    carpeta_usuario = Path.home() if carpeta_usuario is None else carpeta_usuario
    try:
        relativa = python.relative_to(carpeta_usuario.absolute())
    except ValueError:
        return str(python)
    return "${userHome}" + os.sep + str(relativa)


def configuracion_servidor() -> dict:
    return {
        "type": "stdio",
        "command": ruta_python_para_vscode(),
        "args": ["-m", "rag_qa.servidor_mcp"],
    }


class McpJsonNoEditable(RuntimeError):
    """El mcp.json existe pero no se puede leer como JSON: no se toca, se explica cómo editarlo a mano."""


def _instrucciones_a_mano(ruta: Path) -> str:
    """Mensaje en español para agregar el servidor del RAG a mano en un mcp.json que no se pudo leer."""
    bloque = json.dumps({NOMBRE_SERVIDOR: configuracion_servidor()}, indent=2, ensure_ascii=False)
    return (
        f"{ruta} no se pudo leer como JSON (puede tener comentarios // o /* */, comas finales "
        "o un error de formato). No se modificó para no perder tus otros servidores.\n"
        "Para conectar el RAG, agrégalo a mano: ábrelo en VS Code y pega esto dentro de \"servers\": { ... }:\n"
        f"{bloque[1:-1].strip()}"
    )


def _guardar_respaldo(ruta: Path, motivo: str) -> None:
    """Mueve el mcp.json que no se puede usar a mcp.json.<fecha-hora>.bak y avisa por qué.

    La fecha y hora en el nombre evitan pisar un respaldo anterior.
    """
    respaldo = ruta.with_name(f"mcp.json.{time.strftime('%Y%m%d-%H%M%S')}.bak")
    ruta.replace(respaldo)
    print(f"   Aviso: {motivo}; se guardó una copia en {respaldo.name} y se creó uno nuevo.")


def _leer_mcp_json(ruta: Path) -> dict:
    """Lee el mcp.json existente. Si tiene otro formato, lo respalda y devuelve uno vacío.

    Si no es JSON (por ejemplo JSONC con comentarios, que VS Code acepta), no se
    toca: se lanza McpJsonNoEditable con las instrucciones para editarlo a mano.
    """
    if ruta.is_symlink():
        # Seguridad: no escribir a través de un enlace (podría apuntar a otro archivo).
        _guardar_respaldo(ruta, "mcp.json era un enlace simbólico")
        return {}
    if not ruta.exists():
        return {}
    try:
        # utf-8-sig: acepta la marca BOM que agrega PowerShell 5.1.
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise McpJsonNoEditable(_instrucciones_a_mano(ruta)) from e
    if not isinstance(datos, dict) or not isinstance(datos.get("servers", {}), dict):
        _guardar_respaldo(ruta, "mcp.json no tenía el formato esperado")
        return {}
    return datos


def _revisar_carpeta_vscode(carpeta: Path, carpeta_workspace: Path) -> None:
    """Seguridad: .vscode no puede ser un enlace ni una unión (junction) hacia otra carpeta."""
    es_union = getattr(carpeta, "is_junction", lambda: False)()  # is_junction existe desde Python 3.12
    fuera_del_workspace = carpeta.resolve() != carpeta_workspace.resolve() / ".vscode"
    if carpeta.is_symlink() or es_union or fuera_del_workspace:
        raise RuntimeError(f"{carpeta} es un enlace: no se escribe mcp.json por seguridad.")


def escribir_mcp_json(carpeta_workspace: Path) -> Path:
    """Crea o actualiza .vscode/mcp.json sin borrar otros servidores que ya existan."""
    ruta = carpeta_workspace / ".vscode" / "mcp.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    _revisar_carpeta_vscode(ruta.parent, carpeta_workspace)
    datos = _leer_mcp_json(ruta)
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
    resultados = herramientas.indice.buscar(
        "Error: locator.click: Timeout 30000ms exceeded", max_resultados=1
    )
    if not resultados:
        print(
            "\nERROR: la consulta de prueba no encontró nada. Revisa que knowledge-base/ tenga "
            "documentos y ejecuta: python scripts/validar_documentos.py"
        )
        return 1
    print(f"   Encontró: {resultados[0].fragmento.metadatos['seccion']}")

    workspace = RAIZ_PROYECTO.parent
    try:
        ruta = escribir_mcp_json(workspace)
        print(f"\n-> Copilot configurado en: {ruta}")
    except McpJsonNoEditable as e:
        print(f"\n-> Aviso: {e}")
    except RuntimeError as e:
        # Por ejemplo: .vscode es un enlace a otra carpeta. No se escribe nada por seguridad.
        print(f"\n-> Aviso: no se configuró Copilot. {e}")
        print("   Solución: borra el enlace .vscode, crea una carpeta normal con ese nombre"
              " y vuelve a ejecutar instalar.bat.")

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
