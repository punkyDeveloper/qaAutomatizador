"""RAG de calidad de software para pruebas de front con Playwright + POM.

Módulos:
- config:       rutas y modelo (configurables con variables de entorno).
- documentos:   lee knowledge-base/ y lo parte en secciones.
- lexico:       búsqueda por palabras clave (BM25).
- embeddings:   convierte texto en vectores (modelo local).
- indice:       guarda los vectores en Chroma y hace la búsqueda híbrida.
- herramientas: las 4 funciones del asistente (revisar, diagnosticar, plantilla, buscar).
- servidor_mcp: expone las herramientas a GitHub Copilot.
"""

__version__ = "1.0.0"
