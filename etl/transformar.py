"""Etapa 2 - TRANSFORMAR: limpia la fuente y arma dimensiones y hechos del modelo estrella.

Entra: la hoja 'Base De Datos' y el catalogo de codigos tal como vienen en el Excel.
Sale:  un objeto Resultado con las tablas listas para cargar y la bitacora de limpieza.
"""
import re
from dataclasses import dataclass, field
from datetime import date

import pandas as pd

import config
from limpiar import (DESCONOCIDO, SIN_DETALLE, SIN_SUBCODIGO, clave_area, clave_turno,
                     estandarizar_referencia, limpiar_operario, normalizar_subcodigo,
                     turno_no_reconocido)

HOJA = "Base De Datos"
AREA_PROGRAMADO = "Paro programado"
# El Excel nombra 1.1 "FALLA MECANICA" en el catalogo, pero los datos y los graficos del
# P-MTO-22 lo usan como "Sistema alimentador de envases"; se respeta el uso real.
NOMBRE_SUBSISTEMA = {"1.1": "Sistema alimentador de envases"}
CODIGO_18 = ("Desinfección", AREA_PROGRAMADO)   # existe en el formulario pero no en la tabla de codigos
HORAS_COLS = [f"h_{n}" for n in config.CODIGOS_PARO]


@dataclass
class Resultado:
    dims: dict[str, pd.DataFrame]
    fact_produccion: pd.DataFrame
    fact_paro: pd.DataFrame
    pii: pd.DataFrame
    incidencias: pd.DataFrame
    bitacora: list[dict] = field(default_factory=list)
    fuente: dict = field(default_factory=dict)       # totales de la fuente cruda
    descartado: dict = field(default_factory=dict)   # totales de lo eliminado (duplicados)
    esperado_prod: pd.DataFrame | None = None        # pacas y horas esperadas por maquina y anio
    esperado_paro: pd.DataFrame | None = None        # horas de paro esperadas por maquina y anio


# ----------------------------------------------------------------------------- utilidades
def _totales(df: pd.DataFrame) -> dict:
    """Sumas que luego se cuadran contra la base de datos."""
    return {
        "filas": len(df),
        "pacas": float(df["pacas"].sum()),
        "horas_trabajadas": float(df["horas_trabajadas"].sum()),
        "tiempo_paro": float(df["tiempo_paro"].sum()),
        "por_codigo": {n: float(df[f"h_{n}"].sum()) for n in config.CODIGOS_PARO},
    }


def _capitalizar(texto: str) -> str:
    """'SISTEMA DE TAPADO' -> 'Sistema de tapado'; si ya trae minusculas se deja igual."""
    t = " ".join(texto.split())
    return t.capitalize() if t.isupper() else t


# -------------------------------------------------------------------------- dimension paro
def construir_dim_paro(catalogo: pd.DataFrame) -> pd.DataFrame:
    """Jerarquia desnormalizada: area -> codigo -> subsistema -> detalle (una fila por hoja)."""
    codigos: dict[int, tuple[str, str]] = {}
    subsistemas: dict[tuple[int, str], str] = {}
    detalles: dict[tuple[str, str], str] = {}

    def celda(i: int, j: int) -> str | None:
        v = catalogo.iloc[i, j]
        return None if pd.isna(v) else " ".join(str(v).split())

    for i in range(len(catalogo)):
        area, col5, col7 = celda(i, 4), celda(i, 5), celda(i, 7)
        if col5:
            if m := re.match(r"^\[(\d+)\]\s*(.+)$", col5):
                codigos[int(m[1])] = (m[2], area)
            elif m := re.match(r"^([35])\.(\d+)\s+(.+)$", col5):
                subsistemas[(int(m[1]), f"{m[1]}.{m[2]}")] = _capitalizar(m[3])
        if col7:
            if m := re.match(r"^1\.(\d+)\.([A-Za-z0-9])\s+(.+)$", col7):
                letra = {"3": "C"}.get(m[2], m[2].upper())
                detalles[(f"1.{m[1]}", f"1.{m[1]}.{letra}")] = _capitalizar(m[3])
            elif m := re.match(r"^1\.(\d+)\s+(.+)$", col7):
                subsistemas[(1, f"1.{m[1]}")] = _capitalizar(m[2])
    codigos[18] = CODIGO_18
    for sub, nombre in NOMBRE_SUBSISTEMA.items():
        subsistemas[(1, sub)] = nombre

    filas = []

    def agregar(c, sub_cod, sub_nom, det_cod, det_nom):
        nombre, area = codigos[c]
        filas.append({
            "area_impacto": area, "codigo_paro": c, "nombre_codigo": nombre,
            "es_programado": area == AREA_PROGRAMADO or c in config.CODIGOS_PROGRAMADOS_ADICIONALES,
            "subsistema_codigo": sub_cod, "subsistema_nombre": sub_nom,
            "detalle_codigo": det_cod, "detalle_nombre": det_nom,
        })

    for c in sorted(codigos):
        agregar(c, SIN_SUBCODIGO, SIN_SUBCODIGO, SIN_SUBCODIGO, SIN_SUBCODIGO)
        propios = sorted((k for k in subsistemas if k[0] == c), key=lambda k: int(k[1].split(".")[1]))
        for _, sub in propios:
            agregar(c, sub, subsistemas[(c, sub)], SIN_DETALLE, SIN_DETALLE)
            for (s2, det) in sorted(k for k in detalles if k[0] == sub):
                agregar(c, sub, subsistemas[(c, sub)], det, detalles[(s2, det)])
    dim = pd.DataFrame(filas)
    dim.insert(0, "paro_key", range(1, len(dim) + 1))
    return dim


# -------------------------------------------------------------------------- velocidad meta
def construir_meta(prod: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Velocidad de referencia (SCD tipo 2): percentil 90 de pacas por hora productiva.

    Una version por maquina, referencia y anio con suficientes jornadas. Ademas, una version
    general por maquina y anio (referencia -1) que sirve de respaldo cuando la referencia
    no tiene suficiente historia.
    """
    base = prod[prod["valida_rendimiento"] & (prod["pacas_producidas"] > 0)].copy()
    base["pph"] = base["pacas_producidas"] / (base["horas_programadas"] - base["horas_paro"])
    p = config.PERCENTIL_VELOCIDAD_REFERENCIA

    def agrupar(df, llaves):
        g = df.groupby(llaves)["pph"].agg(n="size", pacas_por_hora=lambda s: s.quantile(p)).reset_index()
        return g[g["n"] >= config.MIN_OBSERVACIONES_META]

    por_ref = agrupar(base[base["referencia_key"] != DESCONOCIDO], ["maquina_key", "referencia_key", "anio"])
    general = agrupar(base, ["maquina_key", "anio"])
    general.insert(1, "referencia_key", DESCONOCIDO)
    metas = pd.concat([por_ref, general]).sort_values(["maquina_key", "referencia_key", "anio"]).reset_index(drop=True)
    metas["pacas_por_hora"] = metas["pacas_por_hora"].round(2)

    ultimo_anio = metas.groupby(["maquina_key", "referencia_key"])["anio"].transform("max")
    metas["vigente_desde"] = metas["anio"].map(lambda a: date(int(a), 1, 1))
    metas["es_vigente"] = metas["anio"] == ultimo_anio
    metas["vigente_hasta"] = [None if v else date(int(a), 12, 31) for v, a in zip(metas["es_vigente"], metas["anio"])]
    metas.insert(0, "meta_key", range(1, len(metas) + 1))
    lookup = {(int(r.maquina_key), int(r.referencia_key), int(r.anio)): int(r.meta_key) for r in metas.itertuples()}
    return metas[["meta_key", "maquina_key", "referencia_key", "pacas_por_hora",
                  "vigente_desde", "vigente_hasta", "es_vigente"]], lookup


# ------------------------------------------------------------------------------ principal
def transformar(base: pd.DataFrame, catalogo: pd.DataFrame) -> Resultado:
    bit: list[dict] = []

    def anotar(regla: str, antes, despues, nota: str = ""):
        bit.append({"regla": regla, "antes": antes, "despues": despues, "nota": nota})

    fuente = _totales(base)

    # 1. Duplicados exactos: misma informacion en las 58 columnas.
    columnas_fuente = [c for c in base.columns if c != "fila_origen"]
    es_dup = base.duplicated(subset=columnas_fuente, keep="first")
    eliminadas = base[es_dup]
    descartado = _totales(eliminadas)
    df = base[~es_dup].copy()
    anotar("Eliminar duplicados exactos", len(base), len(df), f"{len(eliminadas)} filas copia de otra fila")
    incidencias = [
        {"hoja_origen": HOJA, "fila_origen": int(r.fila_origen), "regla": "duplicado_exacto",
         "accion": "fila eliminada", "detalle": f"pacas={r.pacas}, paro={r.tiempo_paro:.2f} h"}
        for r in eliminadas.itertuples()
    ]

    # 2. Separar jornadas (con produccion) de filas de subcodigo (solo detalle de paro).
    es_prod = df["pacas"].notna() | df["horas_trabajadas"].notna()
    anotar("Separar jornadas y filas de subcodigo", len(df), int(es_prod.sum()),
           f"{int((~es_prod).sum())} filas de subcodigo no son jornadas: solo aportan a paros")

    # 3. Atributos limpios.
    df["maquina"] = df["maquina"].astype(str).str.strip()
    df["anio_real"] = df["fecha"].dt.year
    df["fecha_key"] = df["fecha"].dt.year * 10000 + df["fecha"].dt.month * 100 + df["fecha"].dt.day
    df["turno_key"] = df["turno"].map(clave_turno)
    sin_turno = int(((df["turno_key"] == DESCONOCIDO) & es_prod).sum())
    no_rec = int(df["turno"].map(turno_no_reconocido).sum())
    anotar("Unificar turnos", int(base["turno"].nunique(dropna=False)), int(df["turno_key"].nunique()),
           f"valores crudos (incluye nulo) -> turnos distintos; {sin_turno} jornadas quedan 'Sin turno'; "
           f"{no_rec} valores no reconocidos")
    df["area_key"] = df["area_involucrada"].map(clave_area)

    # 4. Dimensiones que vienen del Excel.
    maquinas = sorted(df["maquina"].unique())
    dim_maquina = pd.DataFrame({"maquina_key": range(1, len(maquinas) + 1), "nombre": maquinas,
                                "linea_producto": [m.split("_")[0] for m in maquinas]})
    mapa_maquina = dict(zip(dim_maquina["nombre"], dim_maquina["maquina_key"]))
    df["maquina_key"] = df["maquina"].map(mapa_maquina)

    estandar = df["referencia"].map(estandarizar_referencia)
    df["referencia_std"] = estandar.map(lambda d: d["nombre_estandar"] if d else None)
    refs = (pd.DataFrame([d for d in estandar.dropna()]).drop_duplicates("nombre_estandar")
            .sort_values("nombre_estandar").reset_index(drop=True))
    refs.insert(0, "referencia_key", range(1, len(refs) + 1))
    refs["contenido_cc"] = refs["contenido_cc"].astype("Int64")
    refs["num_colores"] = refs["num_colores"].astype("Int64")
    df["referencia_key"] = df["referencia_std"].map(dict(zip(refs["nombre_estandar"], refs["referencia_key"])))
    df["referencia_key"] = df["referencia_key"].fillna(DESCONOCIDO).astype(int)
    anotar("Estandarizar referencias", int(base["referencia"].nunique()), len(refs),
           f"nombres crudos -> referencias unicas (erratas y formato corregidos); "
           f"{int((df['referencia_key'] == DESCONOCIDO).sum())} filas sin referencia (Desconocida)")

    df["operario_limpio"] = df["operario"].map(limpiar_operario)
    nombres = sorted(df["operario_limpio"].dropna().unique())
    dim_operario = pd.DataFrame({"operario_key": range(1, len(nombres) + 1),
                                 "codigo_seudonimo": [f"OP-{i:03d}" for i in range(1, len(nombres) + 1)],
                                 "activo": True})
    pii = pd.DataFrame({"operario_key": dim_operario["operario_key"], "nombre_original": nombres})
    df["operario_key"] = df["operario_limpio"].map(dict(zip(nombres, dim_operario["operario_key"])))
    df["operario_key"] = df["operario_key"].fillna(DESCONOCIDO).astype(int)
    anotar("Seudonimizar operarios", int(base["operario"].nunique()), len(nombres),
           f"nombres crudos -> operarios con codigo OP-nnn ('No' y 'No aplica' son nulos); "
           f"{int((df['operario_key'] == DESCONOCIDO).sum())} filas sin operario (Desconocido)")

    dim_paro = construir_dim_paro(catalogo)
    llave_paro = {(r.codigo_paro, r.subsistema_codigo, r.detalle_codigo): r.paro_key for r in dim_paro.itertuples()}

    # 5. Hecho de produccion: una fila por jornada.
    prod = df[es_prod].copy()
    prod["horas_programadas"] = prod["horas_trabajadas"].fillna(0)
    prod["horas_paro"] = prod["tiempo_paro"].fillna(0)
    pph = (prod["pacas"] / prod["horas_programadas"]).where(prod["horas_programadas"] > 0)
    atipica = pph > config.UMBRAL_PACAS_POR_HORA_ATIPICO
    prod["pacas_origen"] = prod["pacas"]
    prod["pacas_producidas"] = prod["pacas"].where(~atipica)
    prod["valida_rendimiento"] = prod["pacas_producidas"].notna() & ((prod["horas_programadas"] - prod["horas_paro"]) > 0)

    reglas = {
        "pacas_atipicas": atipica,
        "sin_pacas": prod["pacas"].isna(),
        "sin_horas": prod["horas_trabajadas"].isna(),
        "cero_pacas": prod["pacas"] == 0,
        "cero_horas": prod["horas_trabajadas"] == 0,
        "paro_mayor_horas": prod["horas_paro"] > prod["horas_programadas"],
    }
    prod["bandera_calidad"] = ""
    for nombre, mascara in reglas.items():
        prod.loc[mascara, "bandera_calidad"] = prod.loc[mascara, "bandera_calidad"].map(
            lambda s, n=nombre: f"{s},{n}" if s else n)
    prod["bandera_calidad"] = prod["bandera_calidad"].replace("", None)
    for r in prod[atipica].itertuples():
        incidencias.append({"hoja_origen": HOJA, "fila_origen": int(r.fila_origen), "regla": "pacas_atipicas",
                            "accion": "valor de pacas anulado",
                            "detalle": f"{r.pacas:.0f} pacas en {r.horas_programadas:.1f} h ({r.pacas / r.horas_programadas:.0f} pacas/h)"})
    anotar("Anular pacas atipicas", int(prod["pacas"].notna().sum()), int(prod["pacas_producidas"].notna().sum()),
           f"{int(atipica.sum())} jornadas con mas de {config.UMBRAL_PACAS_POR_HORA_ATIPICO} pacas/h "
           f"({prod.loc[atipica, 'pacas'].sum():,.0f} pacas); se conserva el valor en pacas_origen")
    anotar("Marcar jornadas con datos dudosos", len(prod), int(prod["bandera_calidad"].notna().sum()),
           "se cargan con bandera_calidad: " + ", ".join(f"{k}={int(v.sum())}" for k, v in reglas.items()))
    anotar("Jornadas validas para calcular rendimiento", len(prod), int(prod["valida_rendimiento"].sum()),
           "con pacas validas y horas productivas > 0")

    # 6. Velocidad de referencia (SCD tipo 2) y su asignacion a cada jornada.
    prod["anio"] = prod["anio_real"]
    dim_meta, meta_lookup = construir_meta(prod)

    def asignar(f):
        return meta_lookup.get((f.maquina_key, f.referencia_key, f.anio),
                               meta_lookup.get((f.maquina_key, DESCONOCIDO, f.anio), DESCONOCIDO))

    prod["meta_key"] = [asignar(f) for f in prod.itertuples()]
    propias = sum(1 for f in prod.itertuples() if (f.maquina_key, f.referencia_key, f.anio) in meta_lookup)
    anotar("Calcular velocidad de referencia (SCD tipo 2)", len(prod), len(dim_meta),
           f"{len(dim_meta)} versiones de meta; {propias} jornadas usan la meta de su referencia, "
           f"{len(prod) - propias} usan la general de la maquina")

    fact_produccion = prod[["fecha_key", "maquina_key", "turno_key", "referencia_key", "operario_key", "meta_key",
                            "pacas_producidas", "pacas_origen", "horas_programadas", "horas_paro",
                            "valida_rendimiento", "bandera_calidad", "fila_origen"]].reset_index(drop=True)

    # 7. Hecho de paro: de 18 pares de columnas a una fila por evento.
    llaves = ["fila_origen", "fecha_key", "maquina_key", "turno_key", "referencia_key", "operario_key",
              "area_key", "maquina", "anio_real", "sub_1", "sub_3", "sub_5"]
    ev = df[llaves + HORAS_COLS].melt(id_vars=llaves, value_vars=HORAS_COLS, var_name="codigo", value_name="horas_paro")
    ev["codigo"] = ev["codigo"].str[2:].astype(int)
    ev = ev[ev["horas_paro"].fillna(0) > 0].reset_index(drop=True)
    anotar("Despivotar 18 pares codigo/horas", len(df) * len(HORAS_COLS), len(ev),
           "celdas de codigo -> eventos de paro con horas > 0")

    contadores = {"ok": 0, "legado": 0, "vacio": 0, "no_reconocido": 0, "respaldo": 0}
    paro_keys, areas = [], []
    for f in ev.itertuples():
        texto = {1: f.sub_1, 3: f.sub_3, 5: f.sub_5}.get(f.codigo)
        sub, det, estado = normalizar_subcodigo(f.codigo, texto) if f.codigo in (1, 3, 5) else (None, None, "vacio")
        contadores[estado] += 1
        clave = (f.codigo, sub or SIN_SUBCODIGO, det or (SIN_DETALLE if sub else SIN_SUBCODIGO))
        if clave not in llave_paro:
            contadores["respaldo"] += 1
            clave = (f.codigo, SIN_SUBCODIGO, SIN_SUBCODIGO)
        paro_keys.append(llave_paro[clave])
        areas.append(f.area_key if f.codigo == 5 else DESCONOCIDO)
    ev["paro_key"], ev["area_key"] = paro_keys, areas
    ev["hoja_origen"] = HOJA
    crudos = pd.concat([base["sub_1"], base["sub_3"], base["sub_5"]]).dropna().nunique()
    anotar("Normalizar subcodigos", int(crudos), int(ev["paro_key"].nunique()),
           f"textos crudos -> hojas de jerarquia usadas; eventos: {contadores['ok']} ok, "
           f"{contadores['legado']} del catalogo antiguo (4.x -> 5.x), {contadores['vacio']} sin subcodigo, "
           f"{contadores['no_reconocido']} no reconocidos, {contadores['respaldo']} sin hoja en el catalogo")
    fact_paro = ev[["fecha_key", "maquina_key", "turno_key", "referencia_key", "operario_key", "paro_key",
                    "area_key", "horas_paro", "hoja_origen", "fila_origen"]]
    anotar("Hoja oculta 'Base de datos de Sub codigos'", 1252, 0,
           "no se carga: sus 1.252 filas ya estan todas en 'Base De Datos' (verificado por fecha, maquina, operario y referencia)")

    # 8. Lo que deberia verse en la base, por maquina y anio (para el cuadre).
    esperado_prod = (prod.groupby(["maquina", "anio_real"])
                     .agg(jornadas=("fila_origen", "size"), pacas=("pacas_producidas", "sum"),
                          horas=("horas_programadas", "sum")).reset_index())
    esperado_paro = (ev.groupby(["maquina", "anio_real"])
                     .agg(eventos=("fila_origen", "size"), horas_paro=("horas_paro", "sum")).reset_index())

    dims = {
        "dim_maquina": dim_maquina, "dim_referencia": refs, "dim_operario": dim_operario,
        "dim_paro": dim_paro, "dim_meta_velocidad": dim_meta,
    }
    return Resultado(
        dims=dims, fact_produccion=fact_produccion, fact_paro=fact_paro, pii=pii,
        incidencias=pd.DataFrame(incidencias), bitacora=bit, fuente=fuente, descartado=descartado,
        esperado_prod=esperado_prod, esperado_paro=esperado_paro,
    )
