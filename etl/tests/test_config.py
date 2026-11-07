"""Pruebas unitarias de la configuracion del ETL y parametros de negocio."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config


def test_constantes_negocio():
    """Valida que los parametros del negocio coincidan con las reglas documentadas."""
    assert config.UMBRAL_PACAS_POR_HORA_ATIPICO == 60
    assert config.PERCENTIL_VELOCIDAD_REFERENCIA == 0.90
    assert config.MIN_OBSERVACIONES_META == 10
    assert list(config.CODIGOS_PARO) == list(range(1, 19))
    assert config.CODIGOS_PROGRAMADOS_ADICIONALES == {4, 18}
    assert config.TOLERANCIA == 0.01


def test_rutas_archivos():
    """Valida que las rutas configuradas apunten a los archivos esperados del proyecto."""
    assert config.EXCEL.name == "SEGUIMIENTO_TEMPERAS_Y_VINILOS_Actividad.xlsm"
    assert config.REPORTE_VALIDACION.name == "validacion_etl.md"
    assert config.EXCEL.exists(), f"El archivo Excel debe existir en: {config.EXCEL}"
