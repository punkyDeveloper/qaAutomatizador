# Agente QA para GitHub Copilot

Dos agentes de Copilot para pruebas de front con **Playwright + POM** en JavaScript. Se configuran solo con archivos: **no necesitan instalar nada** (ni Python, ni librerías), por eso sirven en empresas donde los usuarios no tienen permisos de administrador.

| Agente | Para qué | Puede editar archivos |
|---|---|---|
| **QA Revisor** | Revisar código, diagnosticar errores de consola y resolver dudas | No (solo sugiere) |
| **QA Nuevo Proyecto** | Crear un proyecto de pruebas desde cero con la plantilla oficial | Sí |

Los dos se pasan el trabajo con un botón: QA Revisor ofrece "Crear un proyecto desde cero" y QA Nuevo Proyecto ofrece "Revisar el proyecto creado".

## Cómo funciona

```
agente-qa-copilot/
├── .github/
│   ├── agents/
│   │   ├── qa-revisor.agent.md          Agente que revisa y diagnostica
│   │   └── qa-nuevo-proyecto.agent.md   Agente que crea proyectos
│   ├── qa-conocimiento/                 Reglas, convenciones, errores y plantilla del equipo
│   └── copilot-instructions.md          Reglas generales que Copilot sigue siempre
├── .vscode/mcp.json                     (Opcional) conexión al RAG en este computador
├── actualizar-conocimiento.bat          Trae la última versión del conocimiento desde el RAG
└── instalar-en-copilot.bat              Instala los agentes en tu Copilot para todos los proyectos
```

Los agentes trabajan en dos modos, sin configurar nada:

- **Con el RAG** (`rag-qa-playwright` activo): usan sus herramientas, con búsqueda inteligente y detección automática de errores en el código.
- **Sin el RAG** (por ejemplo, en la empresa): leen directamente los documentos de `.github/qa-conocimiento/`.

## Cómo usarlo

1. En VS Code: *Archivo → Abrir carpeta* → `agente-qa-copilot` (o el proyecto donde copiaste la carpeta `.github`).
2. Abre el chat de Copilot (`Ctrl + Alt + I`).
3. En el selector de agentes (donde dice Agent / Ask / Plan) elige **QA Revisor** o **QA Nuevo Proyecto**.
4. Escribe tu pedido. Ejemplos:
   - QA Revisor: "Diagnostica este error:" y pega el error completo.
   - QA Revisor: "Revisa tests/specs/login.spec.js".
   - QA Nuevo Proyecto: "Crea el proyecto en la carpeta mi-proyecto-pruebas".

## Instalarlo en Copilot (para todos tus proyectos)

Haz doble clic en **`instalar-en-copilot.bat`**. Copia los agentes y su conocimiento a tu perfil de Copilot (`%USERPROFILE%\.copilot`). No necesita permisos de administrador.

Después de cerrar y volver a abrir VS Code, **QA Revisor** y **QA Nuevo Proyecto** aparecen en el selector de agentes de **cualquier** proyecto.

- Para actualizarlos (por ejemplo, después de `actualizar-conocimiento.bat`), ejecútalo de nuevo.
- Para desinstalarlos, borra los archivos `qa-*.agent.md` de `%USERPROFILE%\.copilot\agents`, o usa el ícono de papelera en **Configure Custom Agents...**.
- Si abres la carpeta `agente-qa-copilot`, los verás repetidos (los del perfil y los de la carpeta). Es normal.

## Configurarlo desde Copilot

En el selector de agentes elige **Configure Custom Agents...**. Ahí ves los dos agentes, de dónde vienen, y puedes abrirlos para editarlos. Cada agente es un archivo de texto: la parte de arriba (entre `---`) define su nombre, descripción y qué herramientas puede usar; el resto son sus instrucciones.

- Para que un agente **no pueda editar**, no le pongas `edit` en `tools`. Así está QA Revisor.
- Para quitarle el RAG, borra `'rag-qa-playwright/*'` de `tools`.

## Usarlo en otro proyecto o en la empresa

Copia la carpeta **`.github`** completa a la raíz del proyecto de pruebas. No hace falta nada más: al abrir ese proyecto en VS Code, los agentes aparecen en el selector.

Si el proyecto ya tiene una carpeta `.github`, copia dentro solo `agents/`, `qa-conocimiento/` y `copilot-instructions.md` (si ya existe un `copilot-instructions.md`, agrega el contenido al final del existente).

En la empresa, borra `.vscode/mcp.json`: apunta al RAG instalado en este computador y no existirá en otros.

> Los agentes también se pueden publicar a nivel de la organización de GitHub para que toda la empresa los tenga sin copiar archivos. Eso lo configura un administrador de la organización.

## Mantener el conocimiento al día

La fuente oficial es `rag-qa-playwright/knowledge-base`. Cuando se agregue o cambie un documento ahí, haz doble clic en **`actualizar-conocimiento.bat`** para copiar la versión nueva a este agente.
