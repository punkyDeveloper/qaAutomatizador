# qaAutomatizador

Proyecto del equipo para automatizar y mejorar las pruebas de front con **Playwright + Page Object Model** en JavaScript, apoyado por un RAG conectado a GitHub Copilot.

## Contenido

| Carpeta | Qué es |
|---|---|
| `rag-qa-playwright/` | El RAG: base de conocimiento (reglas, convenciones, errores, plantilla), código Python, pruebas e instalador. |
| `.github/copilot-instructions.md` | Reglas que Copilot sigue siempre en este espacio de trabajo. |
| `agente-qa-copilot/` | Agentes de Copilot (QA Revisor y QA Nuevo Proyecto) que funcionan sin instalar nada. Ver su README. |
| `plantilla-playwright-pom/` | Proyecto de pruebas de ejemplo, listo para ejecutar contra Sauce Demo. |

## Estado

- Paso 0 (alcance): cerrado.
- Paso 1 (base de conocimiento): completo, excepto ejemplos reales del proyecto (pendiente).
- Paso 2 (estructura de documentos): completo.
- Pasos 3 a 6 (indexación, búsqueda, evaluación y conexión con Copilot): completos.

## Instalar el RAG

Doble clic en `rag-qa-playwright/instalar.bat`. Al terminar, abre esta carpeta en VS Code,
abre `.vscode/mcp.json`, haz clic en **Start** y usa Copilot en modo **Agent**.
Detalles en `rag-qa-playwright/README.md`.

Detalle de las decisiones: `rag-qa-playwright/docs/paso-0-alcance-rag-qa.md`.
