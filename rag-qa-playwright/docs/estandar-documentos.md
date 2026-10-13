# Estándar de documentos de la base de conocimiento

Este documento explica cómo escribir documentos para `knowledge-base/` de forma que el RAG los encuentre y los use bien. Es para las personas del equipo, no para el RAG (por eso está en `docs/` y no en `knowledge-base/`).

---

## 1. Cómo "lee" el RAG un documento

El RAG no lee los documentos completos. En el Paso 3 los partirá en pedazos, uno por cada sección `##`, y cuando alguien pregunte algo buscará el pedazo más parecido a la pregunta.

Esto tiene una consecuencia importante: **cada sección `##` debe entenderse sola**, sin depender de lo que dice la sección anterior.

```markdown
<!-- Mal: la sección no se entiende sola -->
## Solución
Hacer lo mismo que en el caso anterior.

<!-- Bien: la sección se entiende sola -->
## Error: Timeout en una acción
Playwright esperó a que el elemento estuviera listo y nunca lo estuvo...
```

---

## 2. Bloque de metadatos (obligatorio)

Todo documento empieza con este bloque entre líneas `---`:

```yaml
---
id: js-errores-001
lenguaje: javascript
framework: playwright
runner: "@playwright/test"
tipo: ui
patron: pom
categoria: errores
version: 1.0
---
```

| Campo | Obligatorio | Valores permitidos | Para qué sirve |
|---|---|---|---|
| `id` | Sí | `gen-tema-001` (general) o `js-tema-001` (JavaScript) | Identificar el documento; no se puede repetir |
| `lenguaje` | Sí | `javascript` | Filtrar por lenguaje |
| `framework` | Sí | `playwright` | Filtrar por framework |
| `runner` | No | `"@playwright/test"` | Informativo |
| `tipo` | Sí | `ui` | Filtrar por tipo de prueba |
| `patron` | Sí | `pom` | Filtrar por patrón |
| `categoria` | Sí | ver tabla siguiente | Saber para qué función sirve el documento |
| `version` | Sí | `1.0`, `1.1`, `2.0`... | Saber si el documento se actualizó |

Los valores permitidos son pocos a propósito, porque así lo decidimos en el Paso 0. Si el alcance crece (por ejemplo, se agregan pruebas de API), se agregan valores nuevos aquí y en el validador.

### Categorías

| Categoría | Qué contiene | Función del RAG que la usa |
|---|---|---|
| `buenas-practicas` | Reglas de qué es una buena prueba | 1. Revisar código |
| `convenciones` | Nombres y organización del equipo | 1. Revisar código |
| `errores` | Errores de consola con causa y solución | 2. Explicar errores |
| `comportamiento` | Cómo debe responder el asistente | 3. Solo sugerir |
| `plantilla` | Estructura de proyecto desde cero | 4. Crear estructura |
| `ejemplos` | Código de ejemplo bien y mal hecho | Todas |

---

## 3. Reglas de escritura

1. **Un título principal** (`# `) por documento.
2. **Una idea por sección** (`## `). Si una sección habla de dos cosas, se divide en dos.
3. **Secciones que se entienden solas** (ver punto 1).
4. **Secciones de tamaño razonable**: menos de 4000 caracteres. Una sección muy larga mezcla temas y la búsqueda pierde precisión.
5. **Ejemplos de bien y mal** siempre que se pueda: el contraste ayuda a Copilot a entender la regla.
6. **Nombrar las reglas y convenciones** cuando se aplican (por ejemplo, "Regla 3" o "C2"), para que Copilot las cite.
7. **Usar el mismo formato** que los documentos existentes de la misma categoría. Por ejemplo, un error nuevo sigue el formato del catálogo: mensaje, qué significa, causas, dónde buscar, solución.

---

## 4. Dónde guardar cada documento

```
knowledge-base/
├── general/          Reglas, convenciones y comportamiento (aplican a todo)
└── javascript/
    ├── ui-pom/       Ejemplos de código
    ├── errores/      Catálogos de errores
    └── plantilla/    Plantillas de proyecto
```

---

## 5. Cómo agregar un documento nuevo

1. Copiar `docs/plantilla-nuevo-documento.md` a la carpeta que corresponda.
2. Cambiarle el nombre (minúsculas con guiones, por ejemplo `errores-iframes.md`).
3. Llenar los metadatos con un `id` nuevo.
4. Escribir el contenido siguiendo las reglas de la sección 3.
5. Validar desde la raíz del proyecto:
   ```
   python scripts/validar_documentos.py
   ```
6. Si sale todo en ✅, guardar en Git.

---

## 6. Qué revisa el validador

- **Errores** (hay que corregirlos): falta el bloque de metadatos, falta un campo obligatorio, un valor no permitido, un `id` mal formado o repetido, falta el título principal, no hay secciones `##`.
- **Avisos** (se recomienda corregir): secciones vacías o demasiado largas.
