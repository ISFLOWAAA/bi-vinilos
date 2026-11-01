"""Genera docs/diccionario_datos.md leyendo tipos y llaves directamente de la base.

Uso (con la base levantada):  python etl/diccionario.py

Los tipos, nulos y llaves salen de PostgreSQL, asi que nunca se desfasan del DDL.
La descripcion, el origen y la regla de cada campo se escriben abajo, en NOTAS.
"""
import config

DESTINO = config.RAIZ / "docs" / "diccionario_datos.md"
ESQUEMAS = ("dw", "seguridad", "calidad")
X = "Base De Datos"

# tabla -> (descripcion, origen de la tabla, {columna: origen y regla de transformacion})
NOTAS = {
    "dw.dim_fecha": ("Calendario. Una fila por dia.", "Generada por SQL (`sql/init/02_seed.sql`), 2022-01-01 a 2030-12-31.", {
        "fecha_key": "aaaammdd, p. ej. 20250328.", "fecha": "Dia calendario.", "anio": "Anio de la fecha.",
        "trimestre": "1 a 4.", "mes": "1 a 12.", "nombre_mes": "En espanol, minuscula.", "semana_iso": "Semana ISO 8601.",
        "dia": "Dia del mes.", "dia_semana": "1 = lunes a 7 = domingo.", "nombre_dia": "En espanol, minuscula.",
        "es_fin_semana": "Sabado o domingo.", "anio_mes": "Formato aaaa-mm, para ordenar y filtrar."}),
    "dw.dim_hora": ("Horas del dia, para el monitoreo hora a hora.", "Generada por SQL.", {
        "hora_key": "0 a 23.", "franja": "madrugada (0-5), manana (6-11), tarde (12-17), noche (18-23)."}),
    "dw.dim_maquina": ("Maquinas de envasado.", f"`{X}`.`Maquina`.", {
        "maquina_key": "Llave sustituta; -1 = Desconocida.", "nombre": "Valores distintos de `Maquina`, sin espacios sobrantes.",
        "linea_producto": "Texto antes del guion bajo del nombre (Vinilos_1 -> Vinilos)."}),
    "dw.dim_turno": ("Catalogo limpio de turnos.", "Construida a mano (`sql/init/02_seed.sql`); el ETL mapea el texto crudo con `limpiar.clave_turno`.", {
        "turno_key": "-1 = Sin turno (nulo o 'No aplica' en la fuente; 47 % de las jornadas).", "nombre": "Nombre unico del turno.",
        "tipo_turno": "Turno de 8 h, jornada extendida, turno de 12 h o Desconocido.", "hora_inicio": "Inicio del turno.",
        "hora_fin": "Fin del turno.", "duracion_horas": "Duracion en horas."}),
    "dw.dim_referencia": ("Referencias (productos) envasadas.", f"`{X}`.`Referencia`.", {
        "referencia_key": "Llave sustituta ordenada por nombre; -1 = Desconocida (nulo o 'No aplica').",
        "nombre_estandar": "Nombre con erratas corregidas (Alocdor, Stilo Kids) y formato unico `<producto> <cc>cc (<n> col)`.",
        "producto": "Nombre sin contenido ni colores.", "contenido_cc": "Numero antes de 'cc'; nulo si no aplica.",
        "num_colores": "Numero dentro de '(n col)'; nulo si no aplica."}),
    "dw.dim_operario": ("Operarias y operarios, seudonimizados.", f"`{X}`.`Operario`.", {
        "operario_key": "Llave sustituta; -1 = Desconocido ('No', 'No aplica' o nulo).",
        "codigo_seudonimo": "OP-nnn asignado por orden alfabetico del nombre. El nombre real no esta en este esquema.",
        "activo": "Siempre verdadero (la fuente no informa retiros)."}),
    "dw.dim_paro": ("Jerarquia de paros: area de impacto, codigo, subsistema y detalle. Una fila por hoja.",
                    "Hoja `TABLA CODIGOS` del Excel y el codigo 18 del formulario.", {
        "paro_key": "Llave sustituta; -1 = Sin paro.", "area_impacto": "Columna 'AREA DE IMPACTO' de `TABLA CODIGOS`; el codigo 18 se asigna a Paro programado.",
        "codigo_paro": "Numero entre corchetes: [05] -> 5.", "nombre_codigo": "Texto del codigo sin el prefijo.",
        "es_programado": "Verdadero si el area es Paro programado o el codigo es 4 o 18 (supuesto S5).",
        "subsistema_codigo": "p. ej. 1.2; 'Sin subcodigo' si el codigo no trae subcodigo.",
        "subsistema_nombre": "Del catalogo; 1.1 se nombra como en los datos y graficos del P-MTO-22.",
        "detalle_codigo": "p. ej. 1.2.B (solo codigo 01); 'Sin detalle' si hay subsistema sin detalle.",
        "detalle_nombre": "Del catalogo."}),
    "dw.dim_area_involucrada": ("Quien participa en el paro de ajuste operativo.", "Generada a mano (`sql/init/02_seed.sql`).", {
        "area_key": "-1 = No especificado.", "nombre": "Operarios o Personal de mantenimiento."}),
    "dw.dim_meta_velocidad": ("Velocidad de referencia (pacas por hora) por maquina y referencia. SCD tipo 2.",
                              "Calculada por `transformar.construir_meta` a partir del historico (la fuente no guarda la meta).", {
        "meta_key": "Llave sustituta; -1 = sin meta.", "maquina_key": "Maquina de la meta.",
        "referencia_key": "Referencia de la meta; -1 = general de la maquina (respaldo).",
        "pacas_por_hora": "Percentil 90 de pacas por hora productiva de ese anio, con minimo de 10 jornadas validas.",
        "vigente_desde": "1 de enero del anio de la version.", "vigente_hasta": "31 de diciembre; nulo en la version vigente.",
        "es_vigente": "Verdadero en la version mas reciente de cada maquina y referencia."}),
    "dw.fact_produccion": ("Una fila por jornada: maquina, dia, turno, operario y referencia.",
                           f"`{X}`, filas con pacas u horas trabajadas, despues de eliminar duplicados exactos.", {
        "produccion_id": "Identidad generada por la base.", "fecha_key": "`Fecha` -> aaaammdd.", "maquina_key": "`Maquina` -> dim_maquina.",
        "turno_key": "`Turno` -> `limpiar.clave_turno`.", "referencia_key": "`Referencia` estandarizada; -1 si es nula.",
        "operario_key": "`Operario` limpio; -1 si es nulo.", "meta_key": "Meta de la maquina, referencia y anio; si no existe, la general de la maquina.",
        "pacas_producidas": "`Pacas producidas`; nulo si supera 60 pacas por hora (regla `pacas_atipicas`).",
        "pacas_origen": "`Pacas producidas` tal como viene en el Excel.", "horas_programadas": "`Horas trabajadas`; nulo -> 0.",
        "horas_paro": "`Tiempo de Paro` de la propia fila. No incluye las filas de subcodigo (estan en fact_paro).",
        "horas_productivas": "Calculada: max(horas_programadas - horas_paro, 0).",
        "valida_rendimiento": "Verdadero si pacas_producidas no es nulo y las horas productivas son mayores que 0.",
        "bandera_calidad": "Reglas que aplican: pacas_atipicas, sin_pacas, sin_horas, cero_pacas, cero_horas, paro_mayor_horas.",
        "fila_origen": "Numero de fila en la hoja del Excel, para auditar."}),
    "dw.fact_paro": ("Una fila por evento de paro: jornada o fila de subcodigo, y codigo de paro (con subcodigo si lo tiene).",
                     f"`{X}`, columnas `Codigo N en horas` (N = 1 a 18) despivotadas; se conserva el evento si las horas son mayores que 0.", {
        "paro_id": "Identidad generada por la base.", "fecha_key": "`Fecha` de la fila.", "maquina_key": "`Maquina` de la fila.",
        "turno_key": "`Turno` de la fila.", "referencia_key": "`Referencia` de la fila.", "operario_key": "`Operario` de la fila.",
        "paro_key": "Codigo N + subcodigo normalizado (`limpiar.normalizar_subcodigo`) -> hoja de dim_paro.",
        "area_key": "`Area involucrada en subcodigo 5`, solo para el codigo 5; los demas codigos usan -1.",
        "horas_paro": "`Codigo N en horas`, sin redondear.", "minutos_paro": "Calculada: horas_paro * 60.",
        "eventos": "Siempre 1; sirve para contar fallas (MTBF, MTTR).", "hoja_origen": "Hoja del Excel de la que sale el evento.",
        "fila_origen": "Numero de fila en esa hoja."}),
    "dw.fact_registro_horario": ("Una fila por maquina y hora. Lo alimenta la simulacion para el monitoreo en Grafana.",
                                 "Script de simulacion (fase de Grafana); sin historico.", {
        "registro_id": "Identidad generada por la base.", "fecha_hora": "Inicio de la hora simulada.",
        "fecha_key": "Dia de `fecha_hora`, en aaaammdd.", "hora_key": "Hora (0 a 23) de `fecha_hora`.",
        "maquina_key": "Maquina simulada.", "turno_key": "Turno al que pertenece la hora.",
        "referencia_key": "Referencia que la simulacion asigna a la maquina.",
        "paro_key": "Causa del paro simulado; -1 si la hora no tuvo paro.",
        "meta_key": "Meta vigente de la maquina y referencia en esa fecha.",
        "pacas_hora": "Pacas producidas en la hora.", "minutos_paro": "Minutos de paro dentro de la hora (0 a 60)."}),
    "seguridad.operario_pii": ("Nombre real de cada operario. Acceso restringido; los tableros no lo leen.", f"`{X}`.`Operario`.", {
        "operario_key": "Llave de dim_operario.", "nombre_original": "Nombre sin espacios sobrantes."}),
    "calidad.incidencias": ("Bitacora de correcciones del ETL, una fila por hallazgo.", "Generada por `transformar.py`.", {
        "incidencia_id": "Identidad generada.", "hoja_origen": "Hoja del Excel.", "fila_origen": "Fila en esa hoja.",
        "regla": "duplicado_exacto o pacas_atipicas.", "accion": "Fila eliminada o valor anulado.", "detalle": "Valores afectados."}),
}
ORDEN = list(NOTAS)


def _tipo(c) -> str:
    t = c["data_type"]
    if t == "numeric":
        return f"numeric({c['numeric_precision']},{c['numeric_scale']})" if c["numeric_precision"] else "numeric"
    if t == "character":
        return f"char({c['character_maximum_length']})"
    return {"timestamp without time zone": "timestamp"}.get(t, t)


def main() -> None:
    with config.conectar() as conn, conn.cursor() as cur:
        marcadores = ",".join(["%s"] * len(ESQUEMAS))
        cur.execute(f"""SELECT table_schema||'.'||table_name, column_name, data_type, character_maximum_length,
                               numeric_precision, numeric_scale, is_nullable, is_generated
                        FROM information_schema.columns WHERE table_schema IN ({marcadores})
                        ORDER BY table_schema, table_name, ordinal_position""", ESQUEMAS)
        columnas = [dict(zip(("tabla", "columna", "data_type", "character_maximum_length", "numeric_precision",
                              "numeric_scale", "is_nullable", "is_generated"), f)) for f in cur.fetchall()]
        cur.execute(f"""SELECT tc.table_schema||'.'||tc.table_name, kcu.column_name, tc.constraint_type,
                               ccu.table_schema||'.'||ccu.table_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                        LEFT JOIN information_schema.constraint_column_usage ccu
                          ON tc.constraint_name = ccu.constraint_name AND tc.constraint_type = 'FOREIGN KEY'
                        WHERE tc.constraint_type IN ('PRIMARY KEY','FOREIGN KEY') AND tc.table_schema IN ({marcadores})""",
                    ESQUEMAS)
        llaves: dict[tuple[str, str], str] = {}
        for tabla, col, tipo, ref in cur.fetchall():
            llaves[(tabla, col)] = "PK" if tipo == "PRIMARY KEY" else f"FK -> {ref}"

    salida = ["# Diccionario de datos", "",
              "Generado por `python etl/diccionario.py`. Los tipos y llaves se leen de la base; el origen y las reglas "
              "estan en el propio script. Modelo y justificacion: [modelo_dimensional.md](modelo_dimensional.md). "
              "Reglas de limpieza con conteos: [validacion_etl.md](validacion_etl.md).", ""]
    for tabla in ORDEN:
        descripcion, origen, notas = NOTAS[tabla]
        salida += [f"## `{tabla}`", "", descripcion, "", f"**Origen:** {origen}", "",
                   "| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |", "|---|---|:-:|---|---|"]
        for c in (c for c in columnas if c["tabla"] == tabla):
            tipo = _tipo(c) + (" (calculada)" if c["is_generated"] == "ALWAYS" else "")
            nota = notas.get(c["columna"], "")
            salida.append(f"| `{c['columna']}` | {tipo} | {'si' if c['is_nullable'] == 'YES' else 'no'} | "
                          f"{llaves.get((tabla, c['columna']), '')} | {nota} |")
        salida.append("")
    DESTINO.write_text("\n".join(salida), encoding="utf-8")
    print(f"Diccionario escrito en {DESTINO} ({len(ORDEN)} tablas)")


if __name__ == "__main__":
    main()
