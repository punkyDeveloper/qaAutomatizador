"""Detección automática de anti-patrones conocidos en código de pruebas.

No reemplaza la revisión de Copilot: le da pistas concretas (con número de
línea) y dirige la búsqueda hacia las reglas que aplican.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Patron:
    nombre: str
    regex: re.Pattern
    descripcion: str
    consulta: str      # qué buscar en la base de conocimiento


PATRONES = [
    Patron(
        "espera-fija",
        re.compile(r"waitForTimeout\s*\(|\bsleep\s*\(|setTimeout\s*\("),
        "Espera fija (waitForTimeout/sleep)",
        "Regla 3 nada de esperas fijas waitForTimeout",
    ),
    Patron(
        "selector-fragil",
        re.compile(r"nth-child|xpath=|['\"]\s*//|['\"]/html|\.css-[a-z0-9]+"),
        "Selector frágil (XPath, nth-child o clase generada)",
        "Regla 2 prioridad de locators getByRole selectores frágiles",
    ),
    Patron(
        "selector-en-test",
        re.compile(r"page\.(fill|click|type|check|isVisible|locator)\s*\(\s*['\"`]"),
        "Selector escrito directamente en el test (debería estar en el Page Object)",
        "Regla 1 responsabilidad de cada capa locators en el Page Object",
    ),
    Patron(
        "url-quemada",
        re.compile(r"goto\s*\(\s*['\"`]https?://"),
        "URL completa quemada en el código",
        "Regla 7 datos de prueba URLs quemadas baseURL",
    ),
    Patron(
        "aserción-sin-reintento",
        re.compile(r"expect\s*\(\s*await\b|\.isVisible\s*\(\s*\)?\s*\)\s*\.toBe"),
        "Aserción sin reintento (expect(await ...)); usar aserciones web-first",
        "Regla 3 aserciones web-first expect toBeVisible",
    ),
    Patron(
        "force",
        re.compile(r"force\s*:\s*true"),
        "Uso de { force: true }",
        "intercepts pointer events force true elemento bloqueado",
    ),
    Patron(
        "first-nth",
        re.compile(r"\.(first|last|nth)\s*\("),
        "Uso de .first()/.last()/.nth() (puede esconder un locator ambiguo)",
        "strict mode violation acotar locator first",
    ),
    Patron(
        "condicional",
        re.compile(r"^\s*(if|else)\b|\belse\s*\{"),
        "Lógica condicional (if/else) dentro del código",
        "Regla 8 sin lógica condicional en tests",
    ),
    Patron(
        "clave-quemada",
        re.compile(r"(password|clave|contrase[ñn]a|pass)\w*['\"]?\s*[:=,]\s*['\"][^'\"]{3,}['\"]", re.I),
        "Posible contraseña escrita en el código",
        "Regla 7 datos de prueba credenciales variables de entorno",
    ),
    Patron(
        "nombre-generico",
        re.compile(r"\b(click|llenar|clickBoton)\w*\d\s*\(|\b(btn|input|boton)\d+\b"),
        "Nombre genérico (btn1, clickBoton1): usar nombres con intención",
        "C2 C3 nombres de locators y métodos intención de usuario",
    ),
]


@dataclass
class Senal:
    patron: Patron
    lineas: list[int]


def detectar(codigo: str) -> list[Senal]:
    encontradas: dict[str, Senal] = {}
    for n, linea in enumerate(codigo.splitlines(), 1):
        if linea.strip().startswith("//"):
            continue  # ignorar comentarios
        for p in PATRONES:
            if p.regex.search(linea):
                encontradas.setdefault(p.nombre, Senal(p, [])).lineas.append(n)
    return list(encontradas.values())
