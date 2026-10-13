# Agentes para copiar y pegar en Copilot

Versión de los agentes para empresas donde **no se puede instalar ni ejecutar nada**: cada archivo trae TODO el conocimiento del equipo adentro (reglas, convenciones, errores, ejemplos y plantilla). No depende de otras carpetas ni del RAG.

| Archivo | Agente |
|---|---|
| `qa-revisor.agent.md` | QA Revisor: revisa código, diagnostica errores, responde dudas. No edita archivos. |
| `qa-nuevo-proyecto.agent.md` | QA Nuevo Proyecto: crea un proyecto desde cero con la plantilla. |

## Cómo crearlos desde Copilot

Repite esto para cada archivo:

1. Abre este archivo `.agent.md`, selecciona todo (`Ctrl + A`) y copia (`Ctrl + C`).
2. En el chat de Copilot, abre el selector de agentes (donde dice Agent) y elige **Configure Custom Agents...**.
3. Crea un agente nuevo (botón **+** o **New Agent**).
4. Elige dónde guardarlo:
   - **User profile**: lo tendrás en todos tus proyectos (solo tú).
   - **Workspace**: queda en la carpeta `.github/agents` del proyecto; si el proyecto está en Git, todo el equipo lo recibe.
5. Escribe el nombre del archivo: `qa-revisor` (o `qa-nuevo-proyecto`).
6. Se abre un archivo nuevo: borra lo que traiga, pega (`Ctrl + V`) y guarda (`Ctrl + S`).

El agente aparece de inmediato en el selector.

## Actualizar

Cuando cambie el conocimiento del equipo, estos archivos se regeneran y hay que volver a pegarlos.
