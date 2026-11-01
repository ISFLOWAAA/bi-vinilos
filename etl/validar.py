"""Etapa 4 - VALIDAR: demuestra que lo cargado concuerda con la fuente y escribe el informe.

Regla de cuadre:   fuente = cargado + lo eliminado (duplicados) + lo anulado (pacas atipicas)
Ademas se compara por maquina y anio, y por codigo de paro, para detectar llaves mal asignadas.
"""
import pandas as pd
import psycopg

import config
from transformar import Resultado


def _consultar(conn: psycopg.Connection, sql: str) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(sql)
        return pd.DataFrame(cur.fetchall(), columns=[c.name for c in cur.description]).astype(
            {c.name: float for c in cur.description if c.type_code in (1700, 701, 700)})


def _estado(diferencia: float) -> str:
    return "OK" if abs(diferencia) <= config.TOLERANCIA else "DIFERENCIA"


def validar(conn: psycopg.Connection, r: Resultado) -> tuple[bool, str]:
    """Devuelve (todo_cuadra, informe_en_markdown)."""
    tot = _consultar(conn, """
        SELECT (SELECT count(*) FROM dw.fact_produccion)                          AS jornadas,
               (SELECT count(*) FROM dw.fact_paro)                                AS eventos,
               (SELECT coalesce(sum(pacas_producidas), 0) FROM dw.fact_produccion) AS pacas,
               (SELECT coalesce(sum(pacas_origen), 0) FROM dw.fact_produccion)     AS pacas_origen,
               (SELECT coalesce(sum(horas_programadas), 0) FROM dw.fact_produccion) AS horas,
               (SELECT coalesce(sum(horas_paro), 0) FROM dw.fact_paro)             AS paro,
               (SELECT count(*) FROM calidad.incidencias)                          AS incidencias""").iloc[0]
    por_codigo = _consultar(conn, """
        SELECT p.codigo_paro AS codigo, sum(f.horas_paro) AS horas
        FROM dw.fact_paro f JOIN dw.dim_paro p USING (paro_key) GROUP BY 1 ORDER BY 1""").set_index("codigo")["horas"]
    prod_db = _consultar(conn, """
        SELECT m.nombre AS maquina, d.anio AS anio_real, count(*) AS jornadas,
               coalesce(sum(f.pacas_producidas), 0) AS pacas, sum(f.horas_programadas) AS horas
        FROM dw.fact_produccion f JOIN dw.dim_maquina m USING (maquina_key) JOIN dw.dim_fecha d USING (fecha_key)
        GROUP BY 1, 2""")
    paro_db = _consultar(conn, """
        SELECT m.nombre AS maquina, d.anio AS anio_real, count(*) AS eventos, sum(f.horas_paro) AS horas_paro
        FROM dw.fact_paro f JOIN dw.dim_maquina m USING (maquina_key) JOIN dw.dim_fecha d USING (fecha_key)
        GROUP BY 1, 2""")

    fu, de = r.fuente, r.descartado
    anuladas = float(tot["pacas_origen"] - tot["pacas"])
    verificaciones: list[tuple[str, float, float, float, str]] = []   # nombre, fuente, cargado, ajuste, nota

    def cuadre(nombre, f, cargado, eliminado, anulado=0.0, nota=""):
        verificaciones.append((nombre, f, cargado, eliminado + anulado, nota))

    jornadas_fuente = int(len(r.fact_produccion))
    cuadre("Pacas producidas", fu["pacas"], float(tot["pacas"]), de["pacas"], anuladas,
           "ajuste = pacas de duplicados + pacas atipicas anuladas")
    cuadre("Horas trabajadas (programadas)", fu["horas_trabajadas"], float(tot["horas"]), de["horas_trabajadas"], 0,
           "ajuste = horas de filas duplicadas")
    cuadre("Tiempo de paro (horas)", fu["tiempo_paro"], float(tot["paro"]), de["tiempo_paro"], 0,
           "ajuste = paro de filas duplicadas")
    for n in config.CODIGOS_PARO:
        cuadre(f"Horas del codigo {n:02d}", fu["por_codigo"][n], float(por_codigo.get(n, 0.0)), de["por_codigo"][n])

    lineas = []
    todo_ok = True
    for nombre, f, cargado, ajuste, nota in verificaciones:
        dif = f - cargado - ajuste
        ok = abs(dif) <= config.TOLERANCIA
        todo_ok &= ok
        lineas.append(f"| {nombre} | {f:,.2f} | {ajuste:,.2f} | {cargado:,.2f} | {dif:,.4f} | {_estado(dif)} |")

    # Cuadre por maquina y anio (detecta llaves mal asignadas, no solo totales).
    def comparar(esperado, real, columnas):
        m = esperado.merge(real, on=["maquina", "anio_real"], how="outer", suffixes=("_esp", "_db")).fillna(0)
        dif = max(float((m[f"{c}_esp"] - m[f"{c}_db"]).abs().max()) for c in columnas)
        return m, dif

    _, dif_prod = comparar(r.esperado_prod, prod_db, ["jornadas", "pacas", "horas"])
    _, dif_paro = comparar(r.esperado_paro, paro_db, ["eventos", "horas_paro"])
    ok_prod, ok_paro = dif_prod <= config.TOLERANCIA, dif_paro <= config.TOLERANCIA
    todo_ok &= ok_prod and ok_paro
    grupos_prod, grupos_paro = len(r.esperado_prod), len(r.esperado_paro)

    cuadre_fila = (len(r.fact_produccion) == int(tot["jornadas"])) and (len(r.fact_paro) == int(tot["eventos"]))
    todo_ok &= cuadre_fila

    informe = ["# Validacion del ETL", "",
               "Informe generado automaticamente por `python etl/main.py` (`etl/validar.py`). No editar a mano.", "",
               "## 1. Reglas de limpieza aplicadas (antes y despues)", "",
               "| Regla | Antes | Despues | Detalle |", "|---|---:|---:|---|"]
    informe += [f"| {b['regla']} | {b['antes']:,} | {b['despues']:,} | {b['nota']} |" for b in r.bitacora]
    informe += ["",
                "## 2. Cuadre de totales contra la fuente", "",
                "Regla: **fuente − ajuste = cargado**. El ajuste son las filas duplicadas eliminadas y las pacas atipicas "
                "anuladas (ver seccion 1).", "",
                "| Medida | Fuente (Excel) | Ajuste | Cargado en la base | Diferencia | Estado |",
                "|---|---:|---:|---:|---:|---|"] + lineas
    informe += ["",
                "## 3. Cuadre por maquina y anio", "",
                f"- Produccion: {grupos_prod} combinaciones de maquina y anio comparadas (jornadas, pacas y horas). "
                f"Diferencia maxima: **{dif_prod:.4f}** → {'OK' if ok_prod else 'DIFERENCIA'}.",
                f"- Paros: {grupos_paro} combinaciones comparadas (eventos y horas). "
                f"Diferencia maxima: **{dif_paro:.4f}** → {'OK' if ok_paro else 'DIFERENCIA'}.",
                f"- Filas cargadas: {int(tot['jornadas']):,} jornadas y {int(tot['eventos']):,} eventos de paro "
                f"→ {'OK' if cuadre_fila else 'DIFERENCIA'}.",
                f"- Incidencias de calidad registradas en `calidad.incidencias`: {int(tot['incidencias']):,}.",
                "",
                "## 4. Conclusion", "",
                ("**El proceso cuadra con la fuente.** Toda diferencia entre el Excel y la base esta explicada por "
                 "los duplicados eliminados y las pacas atipicas anuladas, y queda registrada fila por fila en "
                 "`calidad.incidencias`.") if todo_ok else
                "**Hay diferencias sin explicar.** Revisar las filas marcadas como DIFERENCIA antes de usar los datos."]
    return todo_ok, "\n".join(informe) + "\n"
