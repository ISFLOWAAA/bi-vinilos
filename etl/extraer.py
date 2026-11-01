"""Etapa 1 - EXTRAER: lee el Excel tal como viene, sin limpiar nada."""
import re
from pathlib import Path

import pandas as pd

from config import CODIGOS_PARO

FILA_ENCABEZADO = 9  # en el Excel, la fila 9 tiene los titulos; los datos empiezan en la 10


def _renombrar(columna: str) -> str:
    """Convierte los titulos del Excel en nombres cortos y sin tildes."""
    c = " ".join(str(columna).split())
    fijos = {
        "Fecha": "fecha", "Mes": "mes", "Maquina": "maquina", "Operario": "operario",
        "Referencia": "referencia", "Pacas producidas": "pacas", "Horas trabajadas": "horas_trabajadas",
        "Turno": "turno", "Tipo de paro": "tipo_paro", "Tiempo de Paro": "tiempo_paro",
        "Sub Codigo de paro 1": "sub_1", "Subcodigo 3": "sub_3", "Subcodigo 5": "sub_5",
        "Personal involucrado": "personal_involucrado",
    }
    if c in fijos:
        return fijos[c]
    if c.startswith("A") and c.endswith("o") and len(c) == 3:
        return "anio"
    if "rea involucrada" in c:
        return "area_involucrada"
    m = re.fullmatch(r"Codigo (\d+) en horas", c)
    if m:
        return f"h_{m.group(1)}"
    m = re.fullmatch(r"Codigo de paro (\d+)", c)
    if m:
        return f"min_{m.group(1)}"
    return c


def leer_base(ruta: Path) -> pd.DataFrame:
    """Hoja 'Base De Datos': una fila por jornada o por subcodigo de paro."""
    df = pd.read_excel(ruta, sheet_name="Base De Datos", header=FILA_ENCABEZADO - 1)
    df.columns = [_renombrar(c) for c in df.columns]
    df.insert(0, "fila_origen", df.index + FILA_ENCABEZADO + 1)  # numero de fila en el Excel
    df["fecha"] = pd.to_datetime(df["fecha"])
    for n in CODIGOS_PARO:
        df[f"h_{n}"] = pd.to_numeric(df[f"h_{n}"], errors="coerce")
    for col in ("pacas", "horas_trabajadas", "tiempo_paro"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def leer_catalogo_codigos(ruta: Path) -> pd.DataFrame:
    """Hoja 'TABLA CODIGOS': area de impacto, codigos de paro y jerarquia de subcodigos."""
    return pd.read_excel(ruta, sheet_name="TABLA CODIGOS", header=None)
