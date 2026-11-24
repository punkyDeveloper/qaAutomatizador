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
    # Opcionales para afinar la señal y evitar falsos positivos:
    exigir: re.Pattern | None = None    # la línea además debe cumplir esto
    excluir: re.Pattern | None = None   # si la línea cumple esto, no se marca
    solo_page_object: bool = False      # solo se revisa en Page Objects / componentes
    nivel: str = "error"                # "error" o "aviso" (algo a revisar, no un fallo)


# Asignación de una clave: password: 'abc123', clave = "secreto", fill(passwordInput, 'abc123')
# (\w{0,30} con límite: con \w* una línea como "passpasspass..." tardaba segundos).
_ASIGNACION_DE_CLAVE = re.compile(
    r"(password|clave|contrase[ñn]a|pass)\w{0,30}['\"]?\s*[:=,]\s*['\"][^'\"]{3,}['\"]", re.I
)
# Valor de prueba negativa (usuario inválido): 'clave_incorrecta', 'wrong_pass', 'invalida'.
# Acotada: como mucho 60 caracteres entre la comilla y la palabra.
_VALOR_DE_PRUEBA_NEGATIVA = re.compile(
    r"['\"][^'\"]{0,60}(incorrect|inv[aá]lid|wrong|err[oó]ne)", re.I
)
# Clave de demo pública y documentada (por ejemplo CLAVE_DEMO = 'secret_sauce').
_ES_DEMO = re.compile(r"demo", re.I)


PATRONES = [
    Patron(
        "espera-fija",
        re.compile(r"waitForTimeout\s*\(|\bsleep\s*\(|setTimeout\s*\("),
        "Espera fija (waitForTimeout/sleep)",
        "Regla 3 nada de esperas fijas waitForTimeout",
    ),
    # atrapa: 'div:nth-child(2)', 'xpath=//a', "//div", '/html/body', .css-1a2b3c
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
    # atrapa: expect(await x.textContent()), expect(await page.isVisible('.x')).toBe(true)
    Patron(
        "aserción-sin-reintento",
        # Los espacios van acotados ({0,10}) para que la regex no tarde al cuadrado
        # con líneas preparadas como ".isVisible(" seguido de miles de espacios.
        re.compile(r"expect\s*\(\s*await\b|\.isVisible\s{0,10}\(\s{0,10}\)?\s{0,10}\)\s{0,10}\.toBe"),
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
    # atrapa: password: 'abc123', clave = "secreto"; no marca 'clave_incorrecta' ni las de demo.
    Patron(
        "clave-quemada",
        _ASIGNACION_DE_CLAVE,
        "Posible contraseña escrita en el código",
        "Regla 7 datos de prueba credenciales variables de entorno",
        excluir=re.compile(f"{_VALOR_DE_PRUEBA_NEGATIVA.pattern}|{_ES_DEMO.pattern}", re.I),
    ),
    # atrapa: const CLAVE_DEMO = 'secret_sauce' (clave pública de demo: aviso, no error).
    Patron(
        "clave-demo",
        _ASIGNACION_DE_CLAVE,
        "Clave de demo pública en el código: aceptable solo para la demo; "
        "con tu app, ponla en el .env y deja el valor por defecto vacío",
        "Regla 7 datos de prueba credenciales variables de entorno",
        exigir=_ES_DEMO,
        excluir=_VALOR_DE_PRUEBA_NEGATIVA,
        nivel="aviso",
    ),
    # atrapa: await expect(this.mensajeError).toHaveText(m) dentro de LoginPage.
    Patron(
        "expect-en-page-object",
        re.compile(r"\bexpect\s*\("),
        "Aserción (expect) dentro del Page Object: las aserciones van en el test",
        "Regla 1 responsabilidad de cada capa aserciones van en el test no en el Page Object",
        solo_page_object=True,
    ),
    # atrapa: clickBoton1(), llenarCampo2(), btn1, input3
    Patron(
        "nombre-generico",
        re.compile(r"\b(click|llenar|clickBoton)\w{0,40}\d\s*\(|\b(btn|input|boton)\d+\b"),
        "Nombre genérico (btn1, clickBoton1): usar nombres con intención",
        "C2 C3 nombres de locators y métodos intención de usuario",
    ),
]


@dataclass
class Senal:
    patron: Patron
    lineas: list[int]


# Seguridad: solo se revisan los primeros caracteres de cada línea. Una línea
# gigante (código minificado o pegado a propósito) no debe dejar el servidor colgado.
MAX_CARACTERES_POR_LINEA = 2_000


# Un Page Object (o componente) está en pages/ o components/ (con / o con \ de Windows),
# es una clase con constructor(page) o una clase cuyo nombre termina en Page o Component.
_CARPETA_PAGE_OBJECT = re.compile(r"(^|[\\/])(pages|components)[\\/]", re.I)
_ARCHIVO_DE_TEST = re.compile(r"\.(spec|test)\.[jt]sx?$", re.I)
_CONSTRUCTOR_CON_PAGE = re.compile(r"constructor\s*\(\s*page\b")
_CLASE_PAGE_OBJECT = re.compile(r"\bclass\s+\w{0,60}(Page|Component)\b")


def es_page_object(codigo: str, archivo: str | None = None) -> bool:
    """True si el código parece un Page Object o componente (y no un spec)."""
    if archivo:
        if _ARCHIVO_DE_TEST.search(archivo):
            return False
        if _CARPETA_PAGE_OBJECT.search(archivo):
            return True
    return bool(_CONSTRUCTOR_CON_PAGE.search(codigo) or _CLASE_PAGE_OBJECT.search(codigo))


def _linea_cumple(patron: Patron, linea: str) -> bool:
    """Si la línea dispara el patrón (respetando sus condiciones de exigir y excluir)."""
    if not patron.regex.search(linea):
        return False
    if patron.exigir and not patron.exigir.search(linea):
        return False
    return not (patron.excluir and patron.excluir.search(linea))


def detectar(codigo: str, archivo: str | None = None) -> list[Senal]:
    """Recorre el código línea por línea y devuelve qué anti-patrones aparecen y en qué líneas.

    `archivo` (opcional) ayuda a saber si es un Page Object, para las señales que solo aplican ahí.
    """
    page_object = es_page_object(codigo, archivo)
    patrones = [p for p in PATRONES if page_object or not p.solo_page_object]
    encontradas: dict[str, Senal] = {}
    for numero_linea, linea in enumerate(codigo.splitlines(), 1):
        linea = linea[:MAX_CARACTERES_POR_LINEA]
        if linea.strip().startswith("//"):
            continue  # ignorar comentarios
        for patron in patrones:
            if _linea_cumple(patron, linea):
                encontradas.setdefault(patron.nombre, Senal(patron, [])).lineas.append(numero_linea)
    return list(encontradas.values())
