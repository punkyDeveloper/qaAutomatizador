# Manual de instalación y uso – qaAutomatizador

Guía paso a paso para instalar y usar los agentes QA y el RAG que ayudan a crear, revisar y
corregir pruebas de front con **Playwright + Page Object Model (JavaScript)** desde GitHub Copilot.

---

## 1. Qué necesitas

| Requisito | ¿Obligatorio? | Para qué |
|---|---|---|
| Windows 10 u 11 | Sí | El instalador es un `.bat` de Windows. |
| VS Code con GitHub Copilot (chat) | Sí | Donde se usan los agentes. |
| Python 3.10 o superior | No | Solo para el RAG (búsqueda inteligente). Sin Python, los agentes funcionan igual leyendo los documentos. |
| Node.js 20 o superior | No | Solo para ejecutar las pruebas Playwright que crees. |
| Internet | Solo la primera vez | Descarga librerías y el modelo de búsqueda (~470 MB). |

No se necesitan permisos de administrador.

---

## 2. Instalar

1. Abre la carpeta `qaAutomatizador`.
2. Haz **doble clic en `instalar.bat`**.
3. Espera a que termine (la primera vez tarda varios minutos). Verás tres pasos:

| Paso | Qué hace |
|---|---|
| **[1/3] Conocimiento** | Copia las reglas, errores y plantilla oficiales a los agentes. |
| **[2/3] Agentes en Copilot** | Instala **QA Revisor** y **QA Nuevo Proyecto** en tu perfil de Copilot. Antes guarda una copia de lo que tenías. |
| **[3/3] RAG** | Crea el entorno de Python, instala las librerías verificadas, indexa los documentos, configura Copilot y ejecuta las pruebas. |

4. Al final debe decir que todo terminó bien. **Cierra y vuelve a abrir VS Code.**

Qué significa el resultado:

| Mensaje final | Qué pasó | Qué hacer |
|---|---|---|
| Todo listo (código 0) | Agentes y RAG instalados. | Nada. |
| Agentes instalados, RAG no (código 2) | No hay Python 3.10+. | Instala Python desde python.org (marca *Add to PATH*) y vuelve a ejecutar `instalar.bat`. |
| Error (código 1) | Algo falló (internet, permisos de carpeta, pruebas). | Lee el mensaje en pantalla: dice la causa y la solución. |

Puedes ejecutar `instalar.bat` las veces que quieras: también sirve para **actualizar**.

---

## 3. Dónde queda instalado (rutas de Copilot)

`%USERPROFILE%` es tu carpeta de usuario, por ejemplo `C:\Users\tu-usuario`.
Puedes pegar estas rutas en la barra del Explorador de Windows.

| Qué | Ruta |
|---|---|
| **Agentes de Copilot** (QA Revisor y QA Nuevo Proyecto) | `%USERPROFILE%\.copilot\agents` |
| **Conocimiento que leen los agentes** | `%USERPROFILE%\.copilot\qa-conocimiento` |
| **Respaldos** (se guardan los 3 más recientes) | `%USERPROFILE%\.copilot\respaldo-AAAAMMDD-HHMMSS` |
| **Conexión de Copilot con el RAG** (este espacio de trabajo) | `qaAutomatizador\.vscode\mcp.json` |
| **Conexión de Claude Code con el RAG** | `qaAutomatizador\.mcp.json` |
| Entorno de Python del RAG | `%USERPROFILE%\.venvs\rag-qa-playwright` |
| Base de datos de búsqueda del RAG | `%USERPROFILE%\.rag-qa-playwright\chroma_db` |
| Documentos oficiales (la fuente de todo) | `qaAutomatizador\rag-qa-playwright\knowledge-base` |

---

## 4. Activar el RAG en Copilot (una sola vez)

1. En VS Code: *Archivo → Abrir carpeta* → `qaAutomatizador`.
2. Abre `.vscode/mcp.json` y haz clic en **Start** sobre `rag-qa-playwright`.
3. Abre el chat de Copilot (`Ctrl + Alt + I`) y cambia a modo **Agent**.
4. En el ícono de herramientas debe aparecer `rag-qa-playwright`.

Si no aparece **Start**, revisa que el paso [3/3] del instalador haya terminado bien.

---

## 5. Usar los agentes

En el chat de Copilot, abre el selector de agentes (donde dice *Agent*) y elige uno.

### QA Revisor (solo sugiere, no cambia tus archivos)

| Quieres… | Escribe, por ejemplo |
|---|---|
| Revisar una prueba o un Page Object | `Revisa tests/specs/login.spec.js` |
| Entender un error de la consola | `Diagnostica este error:` y pega el error **completo** |
| Resolver una duda | `¿Dónde van las aserciones, en el Page Object o en el test?` |

Responde con el problema, la línea y la regla del equipo que aplica.

### QA Nuevo Proyecto (crea archivos)

| Quieres… | Escribe, por ejemplo |
|---|---|
| Crear un proyecto de pruebas desde cero | `Crea el proyecto en la carpeta mi-proyecto-pruebas` |

Te pide confirmar la carpeta, crea la estructura Playwright + POM y te pide permiso antes de
ejecutar `npm install` y `npx playwright install`. Nunca borra ni sobrescribe archivos existentes.

Después, para probar el proyecto creado:

```
cd mi-proyecto-pruebas
copy .env.example .env
npx playwright test
```

---

## 6. Usarlo en la empresa (sin instalar nada)

- **Opción A:** copia la carpeta `agente-qa-copilot\.github` a la raíz de tu proyecto de pruebas.
  Al abrir ese proyecto en VS Code, los agentes aparecen solos.
- **Opción B:** si no puedes copiar carpetas, usa los archivos de `agente-qa-copilot\copiar-y-pegar`
  (traen todo el conocimiento adentro). Instrucciones en su `LEEME.md`.

Sin el RAG, los agentes leen los documentos directamente: funcionan igual, con búsqueda más simple.

---

## 7. Mantenerlo al día

| Tarea | Cómo |
|---|---|
| Agregar o cambiar una regla, error o ejemplo | Edita o agrega un `.md` en `rag-qa-playwright\knowledge-base` siguiendo `rag-qa-playwright\docs\estandar-documentos.md`. |
| Validar el documento | `python scripts\validar_documentos.py` (desde `rag-qa-playwright`, con el Python del RAG). |
| Llevar el cambio a Copilot | Ejecuta `instalar.bat` otra vez. |
| Comprobar que todo sigue funcionando | Ver la sección 8. |

---

## 8. Comprobar que funciona (pruebas)

Desde `qaAutomatizador\rag-qa-playwright`, con el Python del RAG
(`%USERPROFILE%\.venvs\rag-qa-playwright\Scripts\python.exe`):

| Prueba | Comando | Resultado esperado |
|---|---|---|
| Pruebas del RAG | `python -m pytest -q` | 0 fallos |
| Prueba de automatización de punta a punta (ejecuta Playwright de verdad) | `python pruebas_automatizacion\probar_automatizacion.py` | Todos los casos con ✅ |
| Buscar algo a mano | `rag-qa buscar "strict mode violation"` | La sección del error |

---

## 9. Problemas comunes

| Problema | Solución |
|---|---|
| No aparecen los agentes en Copilot | Cierra y abre VS Code. Revisa que existan los archivos en `%USERPROFILE%\.copilot\agents`. |
| `rag-qa-playwright` no aparece en las herramientas | Abre `.vscode\mcp.json` y pulsa **Start**. Usa el modo **Agent**. |
| El instalador dice que no hay Python | Instala Python 3.10+ con *Add to PATH* y vuelve a ejecutarlo. |
| Error de descarga en el paso [3/3] | Revisa internet (o la VPN/proxy de la empresa) y vuelve a ejecutarlo. |
| Quiero desinstalar los agentes | Borra `qa-*.agent.md` de `%USERPROFILE%\.copilot\agents`. |
| Quiero desinstalar el RAG | Borra `%USERPROFILE%\.venvs\rag-qa-playwright` y `%USERPROFILE%\.rag-qa-playwright`. |

---

## 10. Qué hay en cada carpeta y archivo

```
qaAutomatizador/
├── instalar.bat                 El ÚNICO instalador (ver sección 2).
├── MANUAL.md                    Este manual.
├── README.md                    Resumen corto del proyecto.
├── CLAUDE.md                    Reglas del proyecto para Claude Code (idioma y comandos).
├── .mcp.json                    Conecta Claude Code con el RAG.
├── .gitignore                   Lo que NO se sube a git (.env, reportes, cachés, base de datos).
├── .vscode/
│   └── mcp.json                 Conecta Copilot (VS Code) con el RAG. Botón "Start".
├── .github/
│   ├── copilot-instructions.md  Reglas que Copilot sigue siempre en este espacio de trabajo.
│   └── CODEOWNERS               Quién debe aprobar cambios en carpetas delicadas.
│
├── agente-qa-copilot/           LOS AGENTES DE COPILOT (lo que usa el equipo QA)
│   ├── README.md                Cómo usarlos y configurarlos.
│   ├── .github/agents/
│   │   ├── qa-revisor.agent.md          Agente que revisa código y diagnostica errores (no edita).
│   │   └── qa-nuevo-proyecto.agent.md   Agente que crea proyectos de pruebas desde cero.
│   ├── .github/qa-conocimiento/ Copia del conocimiento oficial (la actualiza instalar.bat).
│   ├── .github/copilot-instructions.md  Reglas generales para Copilot en proyectos que copien esta carpeta.
│   ├── .vscode/mcp.json         Conexión al RAG si abres solo esta carpeta (bórralo en la empresa).
│   └── copiar-y-pegar/          Versión "todo en uno" de los 2 agentes para empresas sin permisos.
│       └── LEEME.md             Cómo crearlos copiando y pegando en Copilot.
│
├── plantilla-playwright-pom/    PROYECTO DE PRUEBAS DE EJEMPLO (Sauce Demo), listo para ejecutar
│   ├── package.json             Librerías (Playwright y dotenv) con versiones fijas.
│   ├── playwright.config.js     Configuración: URL, navegador, reportes.
│   ├── .env.example             Modelo del archivo .env (URL, usuario y clave).
│   ├── .gitignore               Evita subir .env, reportes y trazas.
│   └── tests/
│       ├── pages/               Page Objects: LoginPage.js, HomePage.js (cómo se maneja cada página).
│       ├── components/          Partes repetidas de las páginas: HeaderComponent.js (encabezado).
│       ├── fixtures/pages.js    Entrega los Page Objects listos a cada test.
│       ├── data/usuarios.js     Datos de prueba (leídos del .env).
│       └── specs/login.spec.js  Los tests (las aserciones van aquí).
│
└── rag-qa-playwright/           EL RAG (búsqueda inteligente que usa Copilot)
    ├── README.md                Cómo funciona por dentro.
    ├── pyproject.toml           Librerías de Python y comandos (rag-qa).
    ├── requirements.lock        Versiones exactas con huella de seguridad (hash) que instala instalar.bat.
    ├── knowledge-base/          LA FUENTE OFICIAL DEL CONOCIMIENTO:
    │   ├── general/             · principios POM, convenciones del equipo, comportamiento del asistente.
    │   └── javascript/          · errores comunes, guía POM en JavaScript y plantilla de proyecto.
    ├── docs/
    │   ├── estandar-documentos.md       Cómo escribir un documento nuevo para la base.
    │   └── plantilla-nuevo-documento.md Plantilla para copiar al crear uno.
    ├── scripts/validar_documentos.py    Revisa que los documentos cumplan el estándar.
    ├── src/rag_qa/              El código del RAG:
    │   ├── config.py            · configuración (rutas, modelo).
    │   ├── documentos.py        · lee los documentos y los parte por secciones.
    │   ├── lexico.py            · búsqueda por palabras clave.
    │   ├── embeddings.py        · búsqueda por significado (modelo local).
    │   ├── indice.py            · une las dos búsquedas y guarda el índice.
    │   ├── senales.py           · detecta malas prácticas en el código (con número de línea).
    │   ├── herramientas.py      · las funciones que usa Copilot (revisar, diagnosticar, plantilla, buscar).
    │   ├── servidor_mcp.py      · el servidor que conecta todo con Copilot.
    │   ├── cli.py               · comandos de consola (rag-qa buscar / error / estado / indexar).
    │   └── instalar.py          · últimos pasos de la instalación.
    ├── tests/                   Pruebas automáticas del RAG (pytest), una por módulo
    │                            más test_calidad.py (aciertos de búsqueda) y test_seguridad.py.
    └── pruebas_automatizacion/  Prueba de punta a punta con Playwright real (sección 8).
```

Carpetas que se crean solas y **no se suben a git**: `reportes/` (reportes de los agentes),
`node_modules/`, `playwright-report/`, `test-results/`, `__pycache__/`, `*.egg-info/`.

---

## 11. Seguridad (lo que debes saber)

- Nunca escribas contraseñas reales en el código: van en el archivo `.env`, que no se sube a git.
- La clave `secret_sauce` de la plantilla es pública (demo de Sauce Demo). En una app real, borra
  `USUARIO_DEMO` y `CLAVE_DEMO` de `tests\data\usuarios.js` y usa el `.env`.
- Los reportes y trazas de Playwright (`playwright-report\`, `test-results\`) pueden guardar lo que
  se escribió en los campos, incluida la clave: no los compartas ni los subas.
- Los cambios en la base de conocimiento, los agentes y el instalador requieren revisión
  (`.github\CODEOWNERS`), porque Copilot los lee como instrucciones.
