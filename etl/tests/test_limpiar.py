"""Pruebas de las reglas de limpieza. Ejecutar:  .venv\\Scripts\\python -m pytest etl/tests"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from limpiar import (clave_area, clave_turno, estandarizar_referencia, limpiar_operario,
                     normalizar_subcodigo, turno_no_reconocido)


def test_turnos_se_unifican():
    assert clave_turno("6am-2pm (Turno 1)") == 1
    assert clave_turno("10pm-6am (Turno 3)") == 3
    assert clave_turno("6am-4:30pm") == 4
    assert clave_turno("6pm-6am") == 6


def test_turno_nulo_o_no_aplica_es_desconocido():
    assert clave_turno(None) == -1
    assert clave_turno(float("nan")) == -1
    assert clave_turno("No aplica") == -1
    assert not turno_no_reconocido("No aplica")
    assert turno_no_reconocido("7am-3pm")


def test_operario_nulos_disfrazados():
    assert limpiar_operario("No aplica") is None
    assert limpiar_operario("No") is None
    assert limpiar_operario(pd.NA) is None
    assert limpiar_operario("  Lorena   T. ") == "Lorena T."


def test_area_involucrada():
    assert clave_area("Operarios") == 1
    assert clave_area("Personal_de_mantenimiento") == 2
    assert clave_area(None) == -1


def test_referencia_corrige_erratas_y_formato():
    r = estandarizar_referencia("Alocdor 22cc (6col)")
    assert r["nombre_estandar"] == "Alocolor 22cc (6 col)"
    assert (r["producto"], r["contenido_cc"], r["num_colores"]) == ("Alocolor", 22, 6)
    assert estandarizar_referencia("Stilo Kids 22cc (6 col)")["producto"] == "Estilo Kids"
    assert estandarizar_referencia("Arti 30 cc (7 col)")["nombre_estandar"] == "Arti 30cc (7 col)"


def test_referencia_sin_colores_y_atipicas():
    assert estandarizar_referencia("Parchesitos 125 cc")["nombre_estandar"] == "Parchesitos 125cc"
    assert estandarizar_referencia("Vinilos x 30 Blanco")["contenido_cc"] is None
    assert estandarizar_referencia("No aplica") is None


def test_subcodigo_codigo_1_dos_formatos():
    assert normalizar_subcodigo(1, "1.2.C Cambio de Valvula") == ("1.2", "1.2.C", "ok")
    assert normalizar_subcodigo(1, "1.2C  CAMBIO DE VALVULA") == ("1.2", "1.2.C", "ok")
    assert normalizar_subcodigo(1, "1.5A BANDA") == ("1.5", "1.5.A", "ok")
    assert normalizar_subcodigo(1, "1.4.3 Sensor") == ("1.4", "1.4.C", "ok")
    assert normalizar_subcodigo(1, "1.6 VIDEO JET") == ("1.6", None, "ok")


def test_subcodigo_codigo_3_y_5():
    assert normalizar_subcodigo(3, "3.3 Falla en la red neumatica") == ("3.3", None, "ok")
    assert normalizar_subcodigo(5, "5.11 Lavado de boquilla") == ("5.11", None, "ok")
    assert normalizar_subcodigo(5, "5.10 Purga de color") == ("5.10", None, "ok")


def test_subcodigo_codigo_5_catalogo_antiguo():
    assert normalizar_subcodigo(5, "4.4  TRANSFER Y PISADOR DE TAPADO") == ("5.5", None, "legado")
    assert normalizar_subcodigo(5, "4.2  SISTEMA DOSIFICADOR DE PINTURA") == ("5.2", None, "legado")
    assert normalizar_subcodigo(5, "4.8 SISTEMA DE ETIQUETADO") == ("5.9", None, "legado")


def test_subcodigo_vacio_o_no_reconocido():
    assert normalizar_subcodigo(5, "Sin especificar")[2] == "vacio"
    assert normalizar_subcodigo(1, None)[2] == "vacio"
    assert normalizar_subcodigo(1, "texto libre")[2] == "no_reconocido"
    assert normalizar_subcodigo(3, "5.2 otra cosa")[2] == "no_reconocido"
