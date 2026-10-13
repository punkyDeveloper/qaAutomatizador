"""Las funciones del asistente que Copilot puede usar.

Cada función busca en la base de conocimiento y devuelve un texto (Markdown)
con las instrucciones y el contexto que Copilot necesita para responder
según las reglas del equipo. Copilot es quien redacta la respuesta final.

Funciones (las 4 definidas en el Paso 1):
1. revisar_codigo       -> revisar una prueba o Page Object y dar sugerencias.
2. diagnosticar_error   -> explicar un error de consola, dónde está y cómo resolverlo.
3. (regla) solo sugerir -> va dentro de las instrucciones de cada respuesta.
4. plantilla_proyecto   -> crear la estructura base de un proyecto desde cero.
Además: buscar_conocimiento (consulta libre) y reindexar.
"""

from __future__ import annotations

from .documentos import Documento, fragmentar
from .indice import Indice, Resultado
from .lexico import tokenizar
from .senales import detectar

CATEGORIAS = [
    "buenas-practicas",
    "convenciones",
    "comportamiento",
    "ejemplos",
    "errores",
    "plantilla",
]

MAX_CARACTERES_ENTRADA = 20_000


def _seccion(documentos: list[Documento], categoria: str, inicio: str) -> str:
    """Contenido de la primera sección cuyo título empieza por `inicio`."""
    for doc in documentos:
        if doc.categoria != categoria:
            continue
        for frag in fragmentar(doc):
            if frag.seccion.lower().startswith(inicio.lower()):
                return frag.contenido
    return ""


def _fuente(r: Resultado) -> str:
    m = r.fragmento.metadatos
    return f"`{m['archivo']}` › {m['seccion']}"


def _bloque_resultados(resultados: list[Resultado], titulo: str) -> str:
    if not resultados:
        return f"## {titulo}\n\n(No se encontró contenido relacionado en la base de conocimiento.)\n"
    partes = [f"## {titulo}\n"]
    for i, r in enumerate(resultados, 1):
        partes.append(f"### {i}. {_fuente(r)}\n\n{r.fragmento.contenido}\n")
    return "\n".join(partes)


def _cobertura(consulta: str, texto: str) -> float:
    """Qué fracción de las palabras de la consulta aparecen en el texto."""
    terminos = {t for t in tokenizar(consulta) if not t.isdigit()}
    if not terminos:
        return 0.0
    presentes = set(tokenizar(texto))
    return len(terminos & presentes) / len(terminos)


def _primera_linea_error(error: str) -> str:
    for linea in error.splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("at "):
            return linea[:300]
    return error[:300]


class Herramientas:
    def __init__(self, indice: Indice):
        self.indice = indice

    def _docs(self) -> list[Documento]:
        self.indice.preparar()
        return self.indice.documentos

    def _reglas_generales(self) -> str:
        return _seccion(self._docs(), "comportamiento", "Reglas generales")

    # ------------------------------------------------------------ buscar
    def buscar_conocimiento(
        self, consulta: str, categoria: str | None = None, max_resultados: int = 5
    ) -> str:
        if categoria and categoria not in CATEGORIAS:
            return f"Categoría inválida '{categoria}'. Usa una de: {', '.join(CATEGORIAS)}."
        max_resultados = max(1, min(int(max_resultados or 5), 10))
        resultados = self.indice.buscar(
            consulta[:MAX_CARACTERES_ENTRADA],
            categorias=[categoria] if categoria else None,
            max_resultados=max_resultados,
        )
        return (
            "# Resultados de la base de conocimiento del equipo\n\n"
            "Responde usando este contenido. Si no responde la pregunta, dilo en lugar de inventar.\n\n"
            + _bloque_resultados(resultados, "Secciones encontradas")
        )

    # ----------------------------------------------------- 1. revisar código
    def revisar_codigo(self, codigo: str, archivo: str | None = None) -> str:
        if not (codigo or "").strip():
            return "No se recibió código para revisar. Pide al usuario el código o el archivo."
        docs = self._docs()
        instrucciones = _seccion(docs, "comportamiento", "Función 1")
        solo_sugerir = _seccion(docs, "comportamiento", "Función 3")
        checklist_reglas = _seccion(docs, "buenas-practicas", "Checklist")
        checklist_conv = _seccion(docs, "convenciones", "Checklist")

        # 1) Reglas de los anti-patrones detectados automáticamente.
        senales = detectar(codigo)
        relacionados: list[Resultado] = []
        vistos: set[str] = set()
        for s in senales:
            for r in self.indice.buscar(
                s.patron.consulta, categorias=["buenas-practicas", "convenciones", "errores"], max_resultados=1
            ):
                if r.fragmento.id not in vistos:
                    vistos.add(r.fragmento.id)
                    relacionados.append(r)
        # 2) Lo más parecido al código completo (ejemplos y reglas).
        for r in self.indice.buscar(
            codigo[:MAX_CARACTERES_ENTRADA],
            categorias=["buenas-practicas", "convenciones", "ejemplos"],
            max_resultados=8,
        ):
            if r.fragmento.id not in vistos and len(relacionados) < len(senales) + 4:
                vistos.add(r.fragmento.id)
                relacionados.append(r)
        # Las secciones de checklist ya van completas arriba.
        relacionados = [r for r in relacionados if not r.fragmento.seccion.startswith("Checklist")]

        if senales:
            lista = "\n".join(
                f"- {s.patron.descripcion} — línea(s) {', '.join(map(str, s.lineas))}" for s in senales
            )
            bloque_senales = (
                "## Señales detectadas automáticamente\n\n"
                "Verifícalas en el código antes de reportarlas (pueden ser falsos positivos):\n\n"
                f"{lista}\n\n"
            )
        else:
            bloque_senales = (
                "## Señales detectadas automáticamente\n\n"
                "Ninguna. Revisa igualmente el código contra los checklists.\n\n"
            )

        encabezado = f"Archivo revisado: `{archivo}`\n\n" if archivo else ""
        return (
            "# Revisión de código de pruebas (Playwright + POM)\n\n"
            f"{encabezado}"
            "## Instrucciones para responder\n\n"
            f"{instrucciones}\n\n"
            f"{solo_sugerir}\n\n"
            "## Checklist de reglas\n\n"
            f"{checklist_reglas}\n\n"
            "## Checklist de convenciones\n\n"
            f"{checklist_conv}\n\n"
            + bloque_senales
            + _bloque_resultados(relacionados, "Reglas y ejemplos relacionados con este código")
            + "\n## Reglas generales\n\n"
            + self._reglas_generales()
        )

    # ------------------------------------------------ 2. diagnosticar error
    def diagnosticar_error(self, error: str, codigo_relacionado: str | None = None) -> str:
        if not (error or "").strip():
            return "No se recibió ningún error. Pide al usuario que pegue el error completo de la consola."
        docs = self._docs()
        instrucciones = _seccion(docs, "comportamiento", "Función 2")
        como_leer = _seccion(docs, "errores", "Cómo leer")

        resultados = self.indice.buscar(
            error[:MAX_CARACTERES_ENTRADA], categorias=["errores"], max_resultados=6
        )
        resultados = [r for r in resultados if not r.fragmento.seccion.startswith("Cómo leer")][:3]

        mensaje = _primera_linea_error(error)
        lineas = []
        for r in resultados:
            c = _cobertura(mensaje, r.fragmento.texto)
            nivel = "alta" if c >= 0.5 else "media" if c >= 0.25 else "baja"
            lineas.append(f"- {_fuente(r)}: coincidencia {nivel} ({c:.0%})")
        mejor = max((_cobertura(mensaje, r.fragmento.texto) for r in resultados), default=0)
        aviso = (
            "\n**Atención:** ninguna entrada del catálogo coincide claramente con este error. "
            "Dile al usuario que este error no está en la base de conocimiento del equipo "
            "y da tu mejor análisis.\n"
            if mejor < 0.25
            else ""
        )
        codigo = (
            f"\n## Código relacionado enviado por el usuario\n\n```javascript\n{codigo_relacionado}\n```\n"
            if codigo_relacionado
            else ""
        )
        return (
            "# Diagnóstico de error de Playwright\n\n"
            "## Instrucciones para responder\n\n"
            f"{instrucciones}\n\n"
            "## Cómo ubicar el archivo y la línea\n\n"
            f"{como_leer}\n\n"
            "## Coincidencias en el catálogo de errores\n\n"
            f"Mensaje principal: `{mensaje}`\n\n" + "\n".join(lineas) + "\n" + aviso + "\n"
            + _bloque_resultados(resultados, "Entradas del catálogo de errores")
            + codigo
            + "\n## Reglas generales\n\n"
            + self._reglas_generales()
        )

    # ---------------------------------------------- 4. plantilla de proyecto
    def plantilla_proyecto(self) -> str:
        docs = self._docs()
        instrucciones = _seccion(docs, "comportamiento", "Función 4")
        modo = _seccion(docs, "comportamiento", "Paso previo")
        plantillas = [d for d in docs if d.categoria == "plantilla"]
        if not plantillas:
            return "No hay ninguna plantilla de proyecto en la base de conocimiento."
        cuerpo = "\n\n".join(d.cuerpo.strip() for d in plantillas)
        return (
            "# Crear proyecto de pruebas desde cero\n\n"
            "## Antes de crear: confirmar el modo de trabajo\n\n"
            f"{modo}\n\n"
            "## Instrucciones para responder\n\n"
            f"{instrucciones}\n\n"
            "Crea los archivos EXACTAMENTE como están en la plantilla (con sus comentarios "
            "DEMO: y TODO:), en la carpeta que indique el usuario.\n\n"
            "## Plantilla completa\n\n"
            f"{cuerpo}\n"
        )

    # ---------------------------------------------------------- reindexar
    def reindexar(self) -> str:
        self.indice.preparar(forzar=True)
        return (
            f"Índice reconstruido: {len(self.indice.documentos)} documentos, "
            f"{self.indice.total_fragmentos} secciones (modelo: {self.indice.embedder.nombre})."
        )

    def estado(self) -> str:
        reconstruyo = self.indice.preparar()
        docs = self.indice.documentos
        lineas = [f"- `{d.archivo}` ({d.categoria}, v{d.metadatos.get('version', '?')})" for d in docs]
        return (
            "# Estado del RAG\n\n"
            f"- Documentos: {len(docs)}\n"
            f"- Secciones indexadas: {self.indice.total_fragmentos}\n"
            f"- Modelo de embeddings: {self.indice.embedder.nombre}\n"
            f"- Base de conocimiento: `{self.indice.config.kb_dir}`\n"
            f"- Base vectorial: `{self.indice.config.db_dir}`\n"
            f"- Reindexado en esta consulta: {'sí' if reconstruyo else 'no'}\n\n"
            "## Documentos\n\n" + "\n".join(lineas)
        )
