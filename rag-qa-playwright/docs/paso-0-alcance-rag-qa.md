# Proyecto RAG de Calidad de Software — Paso 0: Alcance

**Estado:** Paso 0 CERRADO. Siguiente: Paso 1 (base de conocimiento).
**Fecha de cierre:** 30 de septiembre de 2026

> Si abres un chat nuevo, pega este documento completo al inicio para que el asistente tenga todo el contexto.

---

## 1. Objetivo del proyecto

Construir un RAG (Retrieval-Augmented Generation) de calidad de software que ayude al equipo a:

- Automatizar pruebas de front.
- Diagnosticar y solucionar errores en las pruebas.
- Validar que el código de pruebas cumpla las buenas prácticas del equipo (patrón POM).

El RAG se conectará a **GitHub Copilot en VS Code** para usarse directamente desde el editor.

---

## 2. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Tipo de pruebas | Solo front (UI) |
| Framework de pruebas | Playwright |
| Patrón de diseño | Page Object Model (POM) |
| Lenguaje de las pruebas | JavaScript (TypeScript opcional, si alguien lo quiere implementar) |
| Runner de pruebas | `@playwright/test` (runner oficial de Playwright) |
| Pruebas de APIs / Screenplay | Fuera del alcance |
| Lenguaje del RAG | Python |
| Modelo que genera respuestas | GitHub Copilot (modo agente en VS Code) |
| Modelo de embeddings | Local y gratuito (librería sentence-transformers) |
| Base vectorial | Chroma (local, sin servidor) |
| Conexión con Copilot | Servidor MCP escrito en Python |
| Plan de Copilot | Versión individual de VS Code (no empresarial) |

---

## 3. Arquitectura resultante

Como Copilot ya genera las respuestas, el RAG **no necesita su propio modelo de lenguaje ni API de pago**. Su único trabajo es buscar.

```
Desarrollador (VS Code, modo Agent)
        │  pregunta / pide generar o revisar una prueba
        ▼
GitHub Copilot
        │  llama a la herramienta MCP
        ▼
Servidor MCP (Python)
        │  busca fragmentos relevantes
        ▼
Chroma (vectores) ◄── embeddings locales ◄── base de conocimiento (.md)
        │
        ▼
Copilot recibe el contexto y responde usando las reglas del equipo
```

Ventaja: ningún código ni documento sale del computador para generar embeddings, y no hay costo de API.

---

## 4. Ruta completa del proyecto

- **Paso 0. Alcance** — ✅ Cerrado (este documento).
- **Paso 1. Base de conocimiento** — Guías de buenas prácticas de Playwright + POM, ejemplos de código bueno y malo, catálogo de errores comunes con solución, convenciones del equipo.
- **Paso 2. Estructurar documentos** — Markdown con metadatos (frontmatter) para filtrar búsquedas.
- **Paso 3. Indexación** — Dividir documentos en fragmentos, generar embeddings y guardarlos en Chroma.
- **Paso 4. Búsqueda** — Lógica de recuperación para tres tareas: generar pruebas, diagnosticar errores y revisar buenas prácticas.
- **Paso 5. Evaluación** — Set de 20–30 preguntas reales con respuesta esperada para medir la calidad.
- **Paso 6. Conexión con Copilot** — Exponer el RAG como servidor MCP y configurarlo en VS Code.

---

## 5. Requisitos para empezar

- Python 3.10 o superior
- Node.js (para Playwright)
- VS Code con la extensión GitHub Copilot (iniciada sesión)
- Git

---

## 6. Notas importantes

- **Las herramientas MCP solo aparecen en modo Agent** de Copilot, no en Ask ni Edit.
- Si el plan es **Copilot Free**, tiene un límite mensual de solicitudes; con uso intenso del equipo podría quedarse corto. Revisarlo en la configuración de la cuenta de GitHub.
- En VS Code, la configuración de servidores MCP usa la clave `servers` dentro de `mcp.json` (no `mcpServers` como otros clientes).

---

## 7. Estructura de la base de conocimiento (ajustada al alcance)

```
knowledge-base/
├── general/
│   ├── playwright-pom-principios.md   ← ya existe (8 reglas + checklist)
│   └── convenciones-equipo.md         ← pendiente
└── javascript/
    ├── ui-pom/
    │   └── playwright-pom-typescript.md  ← ya existe (convertir a JS, TS opcional)
    └── errores/                          ← pendiente
```

Los archivos de Java y Python creados antes del cierre del alcance **se descartan**.

### Reglas ya definidas (en `playwright-pom-principios.md`)
1. Locators y acciones en el Page Object; aserciones en el test.
2. Prioridad de locators: `getByRole` → `getByLabel` → `getByPlaceholder` → `getByText` → `getByTestId` → CSS/XPath (último recurso).
3. Prohibidas las esperas fijas (`waitForTimeout`); usar aserciones web-first.
4. Métodos con intención de usuario (`login()`, no `clickBoton1()`).
5. Componentes reutilizables en clases propias; sin `BasePage` gigante.
6. Tests independientes; autenticación con `storageState` o fixtures.
7. Sin datos sensibles ni URLs quemadas.
8. Sin `if/else` dentro de los tests.

---

## 8. Siguiente paso

**Paso 1: base de conocimiento.** Para empezar se necesita del equipo:

- Ejemplos de pruebas reales del proyecto (buenas y malas).
- Los errores que más se repiten al correr las pruebas.
- Convenciones internas (nombres de archivos, carpetas, estilo).
- Documentación o guías internas existentes, aunque sean informales.
