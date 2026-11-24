"""Pruebas de la configuración de Copilot y del validador de documentos."""

import json
import os
import subprocess
import sys

from rag_qa.config import RAIZ_PROYECTO
from pathlib import Path

import pytest

from rag_qa.instalar import (
    NOMBRE_SERVIDOR,
    McpJsonNoEditable,
    escribir_mcp_json,
    ruta_python_para_vscode,
)


def test_crea_mcp_json_para_copilot(tmp_path):
    ruta = escribir_mcp_json(tmp_path)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    servidor = datos["servers"][NOMBRE_SERVIDOR]
    assert servidor["type"] == "stdio"
    assert servidor["command"] == ruta_python_para_vscode()
    assert servidor["args"] == ["-m", "rag_qa.servidor_mcp"]


def test_mcp_json_no_guarda_el_nombre_del_usuario(tmp_path):
    # El Python del venv suele estar en la carpeta del usuario: debe quedar con ${userHome}.
    usuario = tmp_path / "usuario"
    python = usuario / ".venvs" / "rag-qa-playwright" / "Scripts" / "python.exe"
    ruta = ruta_python_para_vscode(python, usuario)
    assert ruta == "${userHome}" + os.sep + str(Path(".venvs", "rag-qa-playwright", "Scripts", "python.exe"))
    assert "usuario" not in ruta


def test_python_fuera_del_usuario_usa_ruta_absoluta(tmp_path):
    python = tmp_path / "otro" / "python.exe"
    assert ruta_python_para_vscode(python, tmp_path / "usuario") == str(python.absolute())


def test_mcp_json_real_usa_user_home():
    # Con el venv del instalador (dentro del usuario) el comando no debe tener la ruta del usuario.
    if Path(sys.executable).absolute().is_relative_to(Path.home()):
        assert ruta_python_para_vscode().startswith("${userHome}")


def test_no_borra_otros_servidores_de_mcp_json(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text(
        json.dumps({"servers": {"otro": {"type": "http", "url": "https://x"}}}), encoding="utf-8"
    )
    datos = json.loads(escribir_mcp_json(tmp_path).read_text(encoding="utf-8"))
    assert set(datos["servers"]) == {"otro", NOMBRE_SERVIDOR}


def test_mcp_json_invalido_no_se_sobrescribe(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text("{ esto no es json", encoding="utf-8")
    with pytest.raises(McpJsonNoEditable, match="a mano"):
        escribir_mcp_json(tmp_path)
    assert (tmp_path / ".vscode" / "mcp.json").read_text(encoding="utf-8") == "{ esto no es json"


def test_es_idempotente(tmp_path):
    primero = escribir_mcp_json(tmp_path).read_text(encoding="utf-8")
    segundo = escribir_mcp_json(tmp_path).read_text(encoding="utf-8")
    assert primero == segundo


def test_validador_de_documentos_pasa():
    resultado = subprocess.run(
        [sys.executable, str(RAIZ_PROYECTO / "scripts" / "validar_documentos.py")],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},  # emojis en la consola de Windows
    )
    assert resultado.returncode == 0, resultado.stdout + resultado.stderr
    assert "0 errores" in resultado.stdout


# Bug 1: un mcp.json con BOM se lee bien y uno con comentarios (JSONC) no se sobrescribe.
def test_mcp_json_con_bom_conserva_servidores_y_jsonc_no_se_toca(tmp_path):
    ruta = tmp_path / ".vscode" / "mcp.json"
    ruta.parent.mkdir()
    ruta.write_text(json.dumps({"servers": {"otro": {"type": "http", "url": "https://x"}}}), encoding="utf-8-sig")
    datos = json.loads(escribir_mcp_json(tmp_path).read_text(encoding="utf-8"))
    assert set(datos["servers"]) == {"otro", NOMBRE_SERVIDOR}

    jsonc = '{\n  // mis servidores\n  "servers": {"otro": {"type": "http", "url": "https://x"},},\n}\n'
    ruta.write_text(jsonc, encoding="utf-8")
    with pytest.raises(McpJsonNoEditable, match=NOMBRE_SERVIDOR):
        escribir_mcp_json(tmp_path)
    assert ruta.read_text(encoding="utf-8") == jsonc
