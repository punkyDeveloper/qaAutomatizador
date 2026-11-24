# qaAutomatizador – Instrucciones para Claude

Proyecto para automatizar pruebas de front con **Playwright + Page Object Model (JavaScript)**,
apoyado por un **RAG** (`rag-qa-playwright/`) que se conecta a Copilot y a Claude por MCP.

## Reglas para todo el equipo
- Todo en **español**: código (variables, funciones, comentarios), mensajes y reportes.
- El código debe entenderlo **cualquier persona**: nombres claros, funciones cortas,
  un comentario corto que explique el *para qué* de cada archivo y de cada función no obvia.
- Python del RAG: `%USERPROFILE%\.venvs\rag-qa-playwright\Scripts\python.exe`.
- Pruebas del RAG: `cd rag-qa-playwright` y luego `python -m pytest -q`.
- Reportes de prueba: `reportes/AAAA-MM-DD-<tema>.md`.
- Cada agente agrupa su prueba en **un solo comando o script** (para pedir pocos permisos).
