"""Búsqueda por palabras clave (BM25).

Complementa la búsqueda por vectores. Es muy buena para encontrar mensajes
de error exactos ("strict mode violation", "waitForTimeout"), que es justo
donde los vectores a veces fallan.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

# Palabras tan comunes que no ayudan a buscar ("de", "la", "the").
PALABRAS_VACIAS = set(
    """
    a al algo como con de del el en es esa ese eso esta este esto la las lo los
    mas me mi no o para pero por que se si sin sobre su sus te tu un una uno y ya
    hay muy cual cuando donde
    the a an and are as at be by for from has have in is it its of on or that
    this to was were will with not
    """.split()
)

# Qué cuenta como palabra: letras, números y algunos símbolos de código.
_PATRON_PALABRA = re.compile(r"[a-z0-9_@./-]+")


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _formas_extra(parte: str) -> list[str]:
    """Formas aproximadas de una palabra para que coincidan sus variantes.

    - raíz de 5 letras para palabras largas: "nombro", "nombres" y "nombrar"
      comparten "nombr~".
    - singular sencillo: "tests" -> "test", "locators" -> "locator".
    """
    if not parte.isalpha():
        return []
    formas = []
    if len(parte) >= 6:
        formas.append(parte[:5] + "~")
    if len(parte) >= 4 and parte.endswith("s"):
        formas.append(parte[:-1])
    return formas


def tokenizar(texto: str) -> list[str]:
    """Convierte texto en palabras normalizadas.

    - minúsculas y sin tildes ("Contraseña" -> "contrasena")
    - separa camelCase además de conservar la palabra entera
      ("waitForTimeout" -> "waitfortimeout", "wait", "for", "timeout")
    - agrega formas aproximadas (raíz y singular, ver `_formas_extra`)
    """
    texto_camel_separado = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", texto)
    tokens: list[str] = []
    # Se recorre dos veces: el texto original (palabra entera + formas extra) y el
    # texto con camelCase separado (solo las partes, sin formas extra para no duplicar).
    for fuente in (texto, texto_camel_separado):
        es_original = fuente is texto
        for palabra in _PATRON_PALABRA.findall(_sin_tildes(fuente.lower())):
            for parte in re.split(r"[./-]+", palabra):
                if len(parte) >= 2 and parte not in PALABRAS_VACIAS:
                    tokens.append(parte)
                    if es_original:
                        tokens.extend(_formas_extra(parte))
            # Conserva también la palabra completa con puntos o guiones ("login.spec.js").
            palabra = palabra.strip("./-")
            if ("." in palabra or "-" in palabra) and len(palabra) >= 2:
                tokens.append(palabra)
    return tokens


class BM25:
    """Puntúa cada texto según cuántas palabras de la consulta contiene.

    Las palabras raras pesan más que las comunes y los textos largos no ganan
    solo por ser largos.
    """

    def __init__(self, textos: list[str], k1: float = 1.5, b: float = 0.75):
        # k1 = cuánto premia repetir una palabra; b = cuánto castiga los textos
        # largos (valores estándar de BM25).
        self.k1, self.b = k1, b
        self.conteos = [Counter(tokenizar(t)) for t in textos]
        self.largos = [sum(conteo.values()) for conteo in self.conteos]
        self.largo_promedio = (sum(self.largos) / len(self.largos)) if self.largos else 0
        total_textos = len(self.conteos)
        textos_con_palabra: Counter = Counter()
        for conteo in self.conteos:
            textos_con_palabra.update(conteo.keys())
        # Peso de cada palabra: alto si aparece en pocos textos, bajo si está en todos.
        self.peso_palabra = {
            palabra: math.log(1 + (total_textos - cantidad + 0.5) / (cantidad + 0.5))
            for palabra, cantidad in textos_con_palabra.items()
        }

    def puntajes(self, consulta: str) -> list[float]:
        """Devuelve un puntaje por texto (0 = no comparte ninguna palabra)."""
        palabras_consulta = set(tokenizar(consulta))
        resultado = []
        for conteo_palabras, largo in zip(self.conteos, self.largos):
            ajuste_largo = 1 - self.b + self.b * largo / (self.largo_promedio or 1)
            puntaje = 0.0
            for palabra in palabras_consulta:
                veces = conteo_palabras.get(palabra)
                if not veces:
                    continue
                puntaje += (
                    self.peso_palabra[palabra]
                    * veces * (self.k1 + 1)
                    / (veces + self.k1 * ajuste_largo)
                )
            resultado.append(puntaje)
        return resultado
