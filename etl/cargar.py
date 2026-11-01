"""Etapa 3 - CARGAR: escribe las tablas en PostgreSQL.

La carga es de "desde cero": borra lo cargado antes por el ETL y lo vuelve a insertar, todo
dentro de una transaccion (si algo falla, la base queda como estaba). Las tablas fijas
(calendario, horas, turnos, areas) y los miembros "Desconocido" (llave -1) no se tocan.
"""
import pandas as pd
import psycopg

from transformar import Resultado

# Orden de insercion: primero las dimensiones, luego los hechos.
COLUMNAS = {
    "dw.dim_maquina": ["maquina_key", "nombre", "linea_producto"],
    "dw.dim_referencia": ["referencia_key", "nombre_estandar", "producto", "contenido_cc", "num_colores"],
    "dw.dim_operario": ["operario_key", "codigo_seudonimo", "activo"],
    "seguridad.operario_pii": ["operario_key", "nombre_original"],
    "dw.dim_paro": ["paro_key", "area_impacto", "codigo_paro", "nombre_codigo", "es_programado",
                    "subsistema_codigo", "subsistema_nombre", "detalle_codigo", "detalle_nombre"],
    "dw.dim_meta_velocidad": ["meta_key", "maquina_key", "referencia_key", "pacas_por_hora",
                              "vigente_desde", "vigente_hasta", "es_vigente"],
    "dw.fact_produccion": ["fecha_key", "maquina_key", "turno_key", "referencia_key", "operario_key", "meta_key",
                           "pacas_producidas", "pacas_origen", "horas_programadas", "horas_paro",
                           "valida_rendimiento", "bandera_calidad", "fila_origen"],
    "dw.fact_paro": ["fecha_key", "maquina_key", "turno_key", "referencia_key", "operario_key", "paro_key",
                     "area_key", "horas_paro", "hoja_origen", "fila_origen"],
    "calidad.incidencias": ["hoja_origen", "fila_origen", "regla", "accion", "detalle"],
}

# Se borra en este orden (hijos antes que padres); lo que tiene llave -1 se conserva.
LIMPIEZA = [
    "TRUNCATE dw.fact_registro_horario, dw.fact_paro, dw.fact_produccion RESTART IDENTITY",
    "TRUNCATE calidad.incidencias RESTART IDENTITY",
    "DELETE FROM seguridad.operario_pii",
    "DELETE FROM dw.dim_meta_velocidad WHERE meta_key <> -1",
    "DELETE FROM dw.dim_paro WHERE paro_key <> -1",
    "DELETE FROM dw.dim_operario WHERE operario_key <> -1",
    "DELETE FROM dw.dim_referencia WHERE referencia_key <> -1",
    "DELETE FROM dw.dim_maquina WHERE maquina_key <> -1",
]


def _filas(df: pd.DataFrame):
    """Filas como tuplas de tipos de Python, con None en lugar de NaN."""
    for fila in df.astype(object).itertuples(index=False, name=None):
        yield tuple(None if pd.isna(v) else v for v in fila)


def _copiar(cur: psycopg.Cursor, tabla: str, df: pd.DataFrame) -> int:
    columnas = COLUMNAS[tabla]
    with cur.copy(f"COPY {tabla} ({', '.join(columnas)}) FROM STDIN") as copia:
        for fila in _filas(df[columnas]):
            copia.write_row(fila)
    return len(df)


def cargar(conn: psycopg.Connection, r: Resultado) -> dict[str, int]:
    tablas = {
        "dw.dim_maquina": r.dims["dim_maquina"], "dw.dim_referencia": r.dims["dim_referencia"],
        "dw.dim_operario": r.dims["dim_operario"], "seguridad.operario_pii": r.pii,
        "dw.dim_paro": r.dims["dim_paro"], "dw.dim_meta_velocidad": r.dims["dim_meta_velocidad"],
        "dw.fact_produccion": r.fact_produccion, "dw.fact_paro": r.fact_paro,
        "calidad.incidencias": r.incidencias,
    }
    cargadas = {}
    with conn.transaction(), conn.cursor() as cur:
        for sentencia in LIMPIEZA:
            cur.execute(sentencia)
        for tabla in COLUMNAS:
            cargadas[tabla] = _copiar(cur, tabla, tablas[tabla])
    return cargadas
