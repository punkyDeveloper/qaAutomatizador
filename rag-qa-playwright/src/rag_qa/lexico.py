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

STOPWORDS = set(
    """
    a al algo como con de del el en es esa ese eso esta este esto la las lo los
    mas me mi no o para pero por que se si sin sobre su sus te tu un una uno y ya
    hay muy cual cuando donde
    the a an and are as at be by for from has have in is it its of on or that
    this to was were will with not
    """.split()
)

_TOKEN = re.compile(r"[a-z0-9_@./-]+")


def _sin_tildes(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def tokenizar(texto: str) -> list[str]:
    """Convierte texto en palabras normalizadas.

    - minúsculas y sin tildes ("Contraseña" -> "contrasena")
    - separa camelCase además de conservar la palabra entera
      ("waitForTimeout" -> "waitfortimeout", "wait", "for", "timeout")
    - agrega una raíz aproximada de 5 letras para palabras largas,
      así "nombro" encuentra "nombres"
    """
    # Separar camelCase antes de pasar a minúsculas.
    partes_camel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", texto)
    tokens: list[str] = []
    for fuente in (texto, partes_camel):
        for tok in _TOKEN.findall(_sin_tildes(fuente.lower())):
            for sub in re.split(r"[./-]+", tok):
                if len(sub) >= 2 and sub not in STOPWORDS:
                    tokens.append(sub)
                    # Raíz aproximada: "nombro", "nombres" y "nombrar" comparten "nombr~".
                    if fuente is texto and len(sub) >= 6 and sub.isalpha():
                        tokens.append(sub[:5] + "~")
            tok = tok.strip("./-")
            if ("." in tok or "-" in tok) and len(tok) >= 2:
                tokens.append(tok)
    return tokens


class BM25:
    def __init__(self, textos: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenizar(t)) for t in textos]
        self.largos = [sum(d.values()) for d in self.docs]
        self.promedio = (sum(self.largos) / len(self.largos)) if self.largos else 0
        n = len(self.docs)
        df: Counter = Counter()
        for d in self.docs:
            df.update(d.keys())
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def puntajes(self, consulta: str) -> list[float]:
        terminos = set(tokenizar(consulta))
        resultado = []
        for d, largo in zip(self.docs, self.largos):
            s = 0.0
            for t in terminos:
                f = d.get(t)
                if not f:
                    continue
                norm = 1 - self.b + self.b * largo / (self.promedio or 1)
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * norm)
            resultado.append(s)
        return resultado
