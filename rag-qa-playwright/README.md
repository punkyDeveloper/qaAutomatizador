# RAG de Calidad de Software (Playwright + POM)

RAG que ayuda al equipo a crear, revisar y corregir pruebas de front con Playwright y Page Object Model en JavaScript. Se conecta a GitHub Copilot (modo Agent de VS Code) mediante un servidor MCP.

## Instalación (una sola vez)

Requisito: Python 3.10 o superior.

1. Doble clic en **`instalar.bat`** (o ejecútalo desde la terminal).
2. Espera a que termine: instala las librerías, descarga el modelo (~470 MB la primera vez), indexa los documentos, configura Copilot y ejecuta las pruebas.
3. Abre en VS Code la carpeta que contiene este proyecto (`qaAutomatizador`), abre `.vscode/mcp.json` y haz clic en **Start** sobre `rag-qa-playwright`.
4. En el chat de Copilot, cambia a modo **Agent**: en el ícono de herramientas debe aparecer `rag-qa-playwright`.

## Qué puede hacer Copilot con el RAG

| Herramienta | Para qué |
|---|---|
| `revisar_codigo` | Revisa una prueba o Page Object contra las reglas y convenciones, con detección automática de anti-patrones y número de línea. |
| `diagnosticar_error` | Explica un error de consola, dónde está y cómo resolverlo según el catálogo. |
| `plantilla_proyecto` | Entrega la plantilla para crear un proyecto desde cero. |
| `buscar_conocimiento` | Búsqueda libre en reglas, convenciones, ejemplos y errores. |
| `estado` / `reindexar` | Diagnóstico del índice. |

## Cómo funciona

```
Copilot (modo Agent) ──MCP──> servidor_mcp.py ──> herramientas.py
                                                    │
                       búsqueda híbrida (indice.py) ┤ vectores: modelo local multilingual-e5-small + Chroma
                                                    └ palabras clave: BM25 (mensajes de error exactos)
                                                    │
                                          knowledge-base/*.md
```

- Los documentos se parten por secciones `##` (ver `docs/estandar-documentos.md`).
- **El índice se actualiza solo**: si alguien edita o agrega un documento, la siguiente consulta lo reindexa.
- Ningún documento sale del computador: el modelo de embeddings corre local.
- La base vectorial se guarda en `%USERPROFILE%\.rag-qa-playwright\chroma_db` (fuera de OneDrive).

## Estructura

```
rag-qa-playwright/
├── instalar.bat         Instalador para Windows
├── pyproject.toml       Dependencias del proyecto
├── src/rag_qa/          Código del RAG
│   ├── documentos.py    Lee y parte los documentos
│   ├── lexico.py        Búsqueda por palabras clave (BM25)
│   ├── embeddings.py    Modelo de vectores
│   ├── indice.py        Chroma + búsqueda híbrida
│   ├── senales.py       Detección de anti-patrones en código
│   ├── herramientas.py  Las funciones del asistente
│   ├── servidor_mcp.py  Servidor para Copilot
│   ├── cli.py           Comandos de consola (rag-qa)
│   └── instalar.py      Pasos finales de la instalación
├── tests/               Pruebas unitarias y de calidad (pytest)
├── knowledge-base/      La "biblioteca" que consulta el RAG
├── docs/                Decisiones, estándar y plantilla de documentos
└── scripts/             Validador de documentos
```

## Comandos útiles

Con el entorno instalado (`%USERPROFILE%\.venvs\rag-qa-playwright\Scripts\`):

```
rag-qa buscar "strict mode violation"        Probar una búsqueda
rag-qa buscar "nombres de tests" -c convenciones
rag-qa error "Error: No tests found"         Ver lo que recibe Copilot
rag-qa estado                                Documentos e índice
rag-qa indexar                               Reindexar a mano
python -m pytest                             Ejecutar las pruebas
```

## Pruebas

- **Unitarias** (siempre, sin internet): documentos, palabras clave, índice, reindexado automático, detección de anti-patrones, herramientas, servidor MCP (en proceso y por stdio como lo inicia VS Code), configuración de Copilot y validador.
- **De calidad** (`tests/test_calidad.py`): preguntas reales con la sección que debe encontrarse. Los errores exactos se prueban siempre; las preguntas en lenguaje natural usan el modelo real y exigen al menos 80 % de aciertos.

## Cómo agregar un documento a la base de conocimiento

1. Copiar `docs/plantilla-nuevo-documento.md` a la carpeta que corresponda.
2. Llenar los metadatos y el contenido según `docs/estandar-documentos.md`.
3. Validar: `python scripts/validar_documentos.py`
4. Listo: el RAG lo indexa solo en la siguiente consulta. Si es un caso importante, agrega una pregunta a `tests/test_calidad.py`.

## Configuración avanzada (variables de entorno)

| Variable | Por defecto | Uso |
|---|---|---|
| `RAG_QA_KB` | `knowledge-base/` | Otra carpeta de documentos |
| `RAG_QA_DB` | `%USERPROFILE%\.rag-qa-playwright\chroma_db` | Otra ubicación para la base vectorial |
| `RAG_QA_MODELO` | `intfloat/multilingual-e5-small` | Otro modelo de sentence-transformers |
| `RAG_QA_EMBEDDER` | `modelo` | `hash` = sin modelo (solo palabras clave) |

## Estado

- Paso 0 (alcance) ✅ — ver `docs/paso-0-alcance-rag-qa.md`
- Paso 1 (base de conocimiento) ✅ — pendiente 1.6: ejemplos reales del proyecto
- Paso 2 (estructura de documentos) ✅
- Paso 3 (indexación) ✅
- Paso 4 (búsqueda y herramientas) ✅
- Paso 5 (evaluación) ✅
- Paso 6 (conexión con Copilot) ✅
