"""Pruebas unitarias para las funciones de validacion y control de tolerancias del ETL."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from validar import _estado


def test_estado_dentro_de_tolerancia():
    """Diferencias menores o iguales a config.TOLERANCIA (0.01) deben marcarse como OK."""
    assert _estado(0.0) == "OK"
    assert _estado(0.005) == "OK"
    assert _estado(-0.005) == "OK"
    assert _estado(config.TOLERANCIA) == "OK"
    assert _estado(-config.TOLERANCIA) == "OK"


def test_estado_fuera_de_tolerancia():
    """Diferencias superiores al umbral de tolerancia deben alertarse como DIFERENCIA."""
    assert _estado(0.0101) == "DIFERENCIA"
    assert _estado(-0.0101) == "DIFERENCIA"
    assert _estado(1.0) == "DIFERENCIA"
    assert _estado(-50.0) == "DIFERENCIA"


def test_formula_cuadre_sin_discrepancia():
    """Verifica la logica matematica: fuente - cargado - ajuste == 0."""
    fuente = 1500.0
    cargado = 1450.0
    eliminado_o_ajuste = 50.0
    diferencia = fuente - cargado - eliminado_o_ajuste
    assert _estado(diferencia) == "OK"


def test_formula_cuadre_con_discrepancia_detectable():
    """Verifica que una perdida de datos no explicada supere la tolerancia."""
    fuente = 1500.0
    cargado = 1449.0
    eliminado_o_ajuste = 50.0
    diferencia = fuente - cargado - eliminado_o_ajuste
    assert diferencia == 1.0
    assert _estado(diferencia) == "DIFERENCIA"
