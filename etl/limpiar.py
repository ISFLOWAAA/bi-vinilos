"""Reglas de limpieza: funciones pequenas y puras (sin base de datos ni Excel).

Cada funcion recibe un valor crudo del Excel y devuelve el valor limpio. Estan
cubiertas por pruebas en etl/tests/test_limpiar.py.
"""
import re

import pandas as pd

SIN_SUBCODIGO = "Sin subcodigo"   # el codigo de paro no trae subcodigo
SIN_DETALLE = "Sin detalle"       # hay subsistema pero no el detalle (nivel 3)
DESCONOCIDO = -1                  # llave del miembro "Desconocido" de cada dimension


def _texto(valor) -> str | None:
    """Texto sin espacios repetidos; None si esta vacio o es NaN."""
    if valor is None or pd.isna(valor):
        return None
    t = " ".join(str(valor).split())
    return t or None


# --------------------------------------------------------------------------- turno
TURNOS = {
    "6am-2pm (turno 1)": 1,
    "2pm-10pm (turno 2)": 2,
    "10pm-6am (turno 3)": 3,
    "6am-4:30pm": 4,
    "6am-6pm": 5,
    "6pm-6am": 6,
}


def clave_turno(valor) -> int:
    """8 formas de escribir el turno -> 6 turnos; nulo o 'No aplica' -> -1 (Sin turno)."""
    t = _texto(valor)
    return TURNOS.get(t.lower(), DESCONOCIDO) if t else DESCONOCIDO


def turno_no_reconocido(valor) -> bool:
    """True si el texto no es nulo, ni 'No aplica', ni un turno conocido."""
    t = _texto(valor)
    return bool(t) and t.lower() != "no aplica" and t.lower() not in TURNOS


# ------------------------------------------------------------------------ operario
def limpiar_operario(valor) -> str | None:
    """Nombre sin espacios sobrantes; None si es nulo, 'No' o 'No aplica'."""
    t = _texto(valor)
    if not t or t.lower() in {"no", "no aplica"}:
        return None
    return t


# ---------------------------------------------------------------------------- area
AREAS = {"operarios": 1, "personal_de_mantenimiento": 2}


def clave_area(valor) -> int:
    t = _texto(valor)
    return AREAS.get(t.lower(), DESCONOCIDO) if t else DESCONOCIDO


# ------------------------------------------------------------------------ referencia
ERRATAS_PRODUCTO = {"alocdor": "Alocolor", "stilo kids": "Estilo Kids"}
_RE_REFERENCIA = re.compile(r"^(?P<producto>.+?)\s+(?P<cc>\d+)\s*cc(?:\s*\((?P<colores>\d+)\s*col\))?$", re.I)


def estandarizar_referencia(valor) -> dict | None:
    """'Alocdor 22cc (6col)' -> {'nombre_estandar': 'Alocolor 22cc (6 col)', 'producto': 'Alocolor', ...}.

    Corrige erratas conocidas y unifica el formato '<producto> <cc>cc (<n> col)'.
    Devuelve None si el valor es nulo o 'No aplica'.
    """
    t = _texto(valor)
    if not t or t.lower() == "no aplica":
        return None
    m = _RE_REFERENCIA.match(t)
    if not m:  # ej. 'Vinilos x 30 Blanco': se conserva tal cual
        return {"nombre_estandar": t, "producto": t, "contenido_cc": None, "num_colores": None}
    producto = ERRATAS_PRODUCTO.get(m["producto"].lower(), m["producto"])
    cc = int(m["cc"])
    colores = int(m["colores"]) if m["colores"] else None
    nombre = f"{producto} {cc}cc" + (f" ({colores} col)" if colores else "")
    return {"nombre_estandar": nombre, "producto": producto, "contenido_cc": cc, "num_colores": colores}


# ------------------------------------------------------------------------ subcodigo
# El Excel mezcla dos catalogos para el codigo 05: en el antiguo era "4.x" y la numeracion
# no coincide con la actual (el antiguo 4.4 Transfer es hoy el 5.5). Equivalencia por nombre.
LEGADO_CODIGO_5 = {1: 1, 2: 2, 3: 3, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9}
_DETALLE_NUMERICO = {"3": "C"}   # en el catalogo aparece '1.4.3 Sensor' en lugar de '1.4.C'
_RE_SUBCODIGO = re.compile(r"^\s*(\d+)\.(\d+)(?:\.?([A-Za-z0-9]))?(?![A-Za-z0-9])")
_SIN_DATO = {"sin especificar", "no aplica"}


def normalizar_subcodigo(codigo: int, texto) -> tuple[str | None, str | None, str]:
    """Convierte '1.2D  RETENEDORES' o '1.2.D Retenedores' en ('1.2', '1.2.D', 'ok').

    Devuelve (subsistema, detalle, estado). Estado: 'vacio', 'ok', 'legado' (catalogo
    antiguo del codigo 05) o 'no_reconocido'. Solo el codigo 01 tiene nivel de detalle.
    """
    t = _texto(texto)
    if not t or t.lower() in _SIN_DATO:
        return None, None, "vacio"
    m = _RE_SUBCODIGO.match(t)
    if not m:
        return None, None, "no_reconocido"
    mayor, menor, letra = int(m[1]), int(m[2]), m[3]
    estado = "ok"
    if codigo == 5 and mayor == 4:
        if menor not in LEGADO_CODIGO_5:
            return None, None, "no_reconocido"
        mayor, menor, estado = 5, LEGADO_CODIGO_5[menor], "legado"
    if mayor != codigo:
        return None, None, "no_reconocido"
    subsistema = f"{mayor}.{menor}"
    detalle = None
    if codigo == 1 and letra:
        detalle = f"{subsistema}.{_DETALLE_NUMERICO.get(letra, letra.upper())}"
    return subsistema, detalle, estado
