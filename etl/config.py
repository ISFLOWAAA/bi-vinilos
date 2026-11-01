"""Configuracion central del ETL: rutas, parametros de negocio y conexion a la base."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

# --- Rutas ---
EXCEL = RAIZ / "data" / "raw" / "SEGUIMIENTO_TEMPERAS_Y_VINILOS_Actividad.xlsm"
REPORTE_VALIDACION = RAIZ / "docs" / "validacion_etl.md"

# --- Parametros de negocio (documentados en docs/catalogo_indicadores.md y docs/validacion_etl.md) ---
UMBRAL_PACAS_POR_HORA_ATIPICO = 60   # ~1,5 veces el percentil 99 historico (38,9); sobre esto el dato es imposible
PERCENTIL_VELOCIDAD_REFERENCIA = 0.90
MIN_OBSERVACIONES_META = 10          # minimo de jornadas para calcular una velocidad de referencia
CODIGOS_PARO = range(1, 19)          # codigos de paro 1 a 18
CODIGOS_PROGRAMADOS_ADICIONALES = {4, 18}  # ademas de los que el Excel marca como "Paro programado"
TOLERANCIA = 0.01                    # diferencia aceptada en el cuadre de totales


def conectar() -> psycopg.Connection:
    """Abre la conexion a PostgreSQL con las variables del archivo .env."""
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
