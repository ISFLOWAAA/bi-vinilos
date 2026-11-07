"""Pruebas unitarias de funciones puras y estructuras del modulo transformar."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import pytest

from transformar import Resultado, _capitalizar, _totales


def test_capitalizar_texto_mayusculas():
    """Valida la capitalizacion cuando el texto original viene enteramente en mayusculas."""
    assert _capitalizar("SISTEMA DE TAPADO") == "Sistema de tapado"
    assert _capitalizar("   CAMBIO DE FORMATO   ") == "Cambio de formato"
    assert _capitalizar("FALLA MECANICA") == "Falla mecanica"


def test_capitalizar_texto_mixto_se_respeta():
    """Valida que textos que ya traen minusculas o formato propio no se alteren."""
    assert _capitalizar("Sistema de tapado") == "Sistema de tapado"
    assert _capitalizar("Etiquetado y Termoencogible") == "Etiquetado y Termoencogible"


def test_totales_estructura_y_claves():
    """Valida que el resumen de totales contenga todas las claves requeridas para el cuadre."""
    data = {
        "pacas": [100.0, 200.0],
        "horas_trabajadas": [8.0, 7.5],
        "tiempo_paro": [1.0, 0.5],
    }
    for n in range(1, 19):
        data[f"h_{n}"] = [0.0, 0.0]

    df = pd.DataFrame(data)
    totales = _totales(df)

    assert totales["filas"] == 2
    assert totales["pacas"] == 300.0
    assert totales["horas_trabajadas"] == 15.5
    assert totales["tiempo_paro"] == 1.5
    assert len(totales["por_codigo"]) == 18
    assert all(k in totales["por_codigo"] for k in range(1, 19))


def test_resultado_dataclass_inicializacion():
    """Valida que la estructura de datos Resultado se instancie con los campos minimos."""
    res = Resultado(
        dims={},
        fact_produccion=pd.DataFrame(),
        fact_paro=pd.DataFrame(),
        pii=pd.DataFrame(),
        incidencias=pd.DataFrame(),
    )
    assert isinstance(res.bitacora, list)
    assert isinstance(res.fuente, dict)
    assert isinstance(res.descartado, dict)
    assert res.esperado_prod is None
