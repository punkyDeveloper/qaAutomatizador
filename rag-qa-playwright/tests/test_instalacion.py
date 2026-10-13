"""Pruebas de la configuración de Copilot y del validador de documentos."""

import json
import os
import subprocess
import sys

from rag_qa.config import RAIZ_PROYECTO
from rag_qa.instalar import NOMBRE_SERVIDOR, escribir_mcp_json


def test_crea_mcp_json_para_copilot(tmp_path):
    ruta = escribir_mcp_json(tmp_path)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    servidor = datos["servers"][NOMBRE_SERVIDOR]
    assert servidor["type"] == "stdio"
    assert servidor["command"] == sys.executable
    assert servidor["args"] == ["-m", "rag_qa.servidor_mcp"]


def test_no_borra_otros_servidores_de_mcp_json(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text(
        json.dumps({"servers": {"otro": {"type": "http", "url": "https://x"}}}), encoding="utf-8"
    )
    datos = json.loads(escribir_mcp_json(tmp_path).read_text(encoding="utf-8"))
    assert set(datos["servers"]) == {"otro", NOMBRE_SERVIDOR}


def test_respalda_mcp_json_invalido(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "mcp.json").write_text("{ esto no es json", encoding="utf-8")
    escribir_mcp_json(tmp_path)
    assert (tmp_path / ".vscode" / "mcp.json.bak").exists()


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
