# qaAutomatizador

Proyecto del equipo para automatizar y mejorar las pruebas de front con **Playwright + Page Object Model** en JavaScript, apoyado por un RAG conectado a GitHub Copilot.

## Contenido

| Carpeta | Qué es |
|---|---|
| `instalar.bat` | El único instalador. Ver `MANUAL.md`. |
| `rag-qa-playwright/` | El RAG: base de conocimiento (reglas, convenciones, errores, plantilla), código Python y pruebas. |
| `.github/copilot-instructions.md` | Reglas que Copilot sigue siempre en este espacio de trabajo. |
| `agente-qa-copilot/` | Agentes de Copilot (QA Revisor y QA Nuevo Proyecto) que funcionan sin instalar nada. Ver su README. |
| `plantilla-playwright-pom/` | Proyecto de pruebas de ejemplo, listo para ejecutar contra Sauce Demo. |

## Estado

- Paso 0 (alcance): cerrado.
- Paso 1 (base de conocimiento): completo, excepto ejemplos reales del proyecto (pendiente).
- Paso 2 (estructura de documentos): completo.
- Pasos 3 a 6 (indexación, búsqueda, evaluación y conexión con Copilot): completos.

## Instalar (un solo instalador)

Doble clic en **`instalar.bat`**, en esta carpeta (`qaAutomatizador`). Hace tres pasos:

1. Actualiza el conocimiento de los agentes desde `rag-qa-playwright/knowledge-base`.
2. Instala los agentes QA Revisor y QA Nuevo Proyecto en tu Copilot (`%USERPROFILE%\.copilot`). No necesita Python.
3. Instala el RAG (necesita Python 3.10+): librerías, índice, configuración de Copilot y pruebas.

Si no tienes Python, los agentes quedan instalados igual y el instalador explica cómo terminar.
No pide permisos de administrador y se puede ejecutar varias veces.

Al terminar, abre esta carpeta en VS Code, abre `.vscode/mcp.json`, haz clic en **Start** y usa
Copilot en modo **Agent**. Detalles en `rag-qa-playwright/README.md`.

**Manual de instalación y uso, paso a paso: [`MANUAL.md`](MANUAL.md).**
