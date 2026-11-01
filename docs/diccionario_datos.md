# Diccionario de datos

Generado por `python etl/diccionario.py`. Los tipos y llaves se leen de la base; el origen y las reglas estan en el propio script. Modelo y justificacion: [modelo_dimensional.md](modelo_dimensional.md). Reglas de limpieza con conteos: [validacion_etl.md](validacion_etl.md).

## `dw.dim_fecha`

Calendario. Una fila por dia.

**Origen:** Generada por SQL (`sql/init/02_seed.sql`), 2022-01-01 a 2030-12-31.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `fecha_key` | integer | no | PK | aaaammdd, p. ej. 20250328. |
| `fecha` | date | no |  | Dia calendario. |
| `anio` | smallint | no |  | Anio de la fecha. |
| `trimestre` | smallint | no |  | 1 a 4. |
| `mes` | smallint | no |  | 1 a 12. |
| `nombre_mes` | text | no |  | En espanol, minuscula. |
| `semana_iso` | smallint | no |  | Semana ISO 8601. |
| `dia` | smallint | no |  | Dia del mes. |
| `dia_semana` | smallint | no |  | 1 = lunes a 7 = domingo. |
| `nombre_dia` | text | no |  | En espanol, minuscula. |
| `es_fin_semana` | boolean | no |  | Sabado o domingo. |
| `anio_mes` | char(7) | no |  | Formato aaaa-mm, para ordenar y filtrar. |

## `dw.dim_hora`

Horas del dia, para el monitoreo hora a hora.

**Origen:** Generada por SQL.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `hora_key` | smallint | no | PK | 0 a 23. |
| `franja` | text | no |  | madrugada (0-5), manana (6-11), tarde (12-17), noche (18-23). |

## `dw.dim_maquina`

Maquinas de envasado.

**Origen:** `Base De Datos`.`Maquina`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `maquina_key` | integer | no | PK | Llave sustituta; -1 = Desconocida. |
| `nombre` | text | no |  | Valores distintos de `Maquina`, sin espacios sobrantes. |
| `linea_producto` | text | no |  | Texto antes del guion bajo del nombre (Vinilos_1 -> Vinilos). |

## `dw.dim_turno`

Catalogo limpio de turnos.

**Origen:** Construida a mano (`sql/init/02_seed.sql`); el ETL mapea el texto crudo con `limpiar.clave_turno`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `turno_key` | smallint | no | PK | -1 = Sin turno (nulo o 'No aplica' en la fuente; 47 % de las jornadas). |
| `nombre` | text | no |  | Nombre unico del turno. |
| `tipo_turno` | text | no |  | Turno de 8 h, jornada extendida, turno de 12 h o Desconocido. |
| `hora_inicio` | time without time zone | si |  | Inicio del turno. |
| `hora_fin` | time without time zone | si |  | Fin del turno. |
| `duracion_horas` | numeric(4,1) | si |  | Duracion en horas. |

## `dw.dim_referencia`

Referencias (productos) envasadas.

**Origen:** `Base De Datos`.`Referencia`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `referencia_key` | integer | no | PK | Llave sustituta ordenada por nombre; -1 = Desconocida (nulo o 'No aplica'). |
| `nombre_estandar` | text | no |  | Nombre con erratas corregidas (Alocdor, Stilo Kids) y formato unico `<producto> <cc>cc (<n> col)`. |
| `producto` | text | no |  | Nombre sin contenido ni colores. |
| `contenido_cc` | smallint | si |  | Numero antes de 'cc'; nulo si no aplica. |
| `num_colores` | smallint | si |  | Numero dentro de '(n col)'; nulo si no aplica. |

## `dw.dim_operario`

Operarias y operarios, seudonimizados.

**Origen:** `Base De Datos`.`Operario`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `operario_key` | integer | no | PK | Llave sustituta; -1 = Desconocido ('No', 'No aplica' o nulo). |
| `codigo_seudonimo` | text | no |  | OP-nnn asignado por orden alfabetico del nombre. El nombre real no esta en este esquema. |
| `activo` | boolean | no |  | Siempre verdadero (la fuente no informa retiros). |

## `dw.dim_paro`

Jerarquia de paros: area de impacto, codigo, subsistema y detalle. Una fila por hoja.

**Origen:** Hoja `TABLA CODIGOS` del Excel y el codigo 18 del formulario.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `paro_key` | integer | no | PK | Llave sustituta; -1 = Sin paro. |
| `area_impacto` | text | no |  | Columna 'AREA DE IMPACTO' de `TABLA CODIGOS`; el codigo 18 se asigna a Paro programado. |
| `codigo_paro` | smallint | no |  | Numero entre corchetes: [05] -> 5. |
| `nombre_codigo` | text | no |  | Texto del codigo sin el prefijo. |
| `es_programado` | boolean | no |  | Verdadero si el area es Paro programado o el codigo es 4 o 18 (supuesto S5). |
| `subsistema_codigo` | text | no |  | p. ej. 1.2; 'Sin subcodigo' si el codigo no trae subcodigo. |
| `subsistema_nombre` | text | no |  | Del catalogo; 1.1 se nombra como en los datos y graficos del P-MTO-22. |
| `detalle_codigo` | text | no |  | p. ej. 1.2.B (solo codigo 01); 'Sin detalle' si hay subsistema sin detalle. |
| `detalle_nombre` | text | no |  | Del catalogo. |

## `dw.dim_area_involucrada`

Quien participa en el paro de ajuste operativo.

**Origen:** Generada a mano (`sql/init/02_seed.sql`).

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `area_key` | smallint | no | PK | -1 = No especificado. |
| `nombre` | text | no |  | Operarios o Personal de mantenimiento. |

## `dw.dim_meta_velocidad`

Velocidad de referencia (pacas por hora) por maquina y referencia. SCD tipo 2.

**Origen:** Calculada por `transformar.construir_meta` a partir del historico (la fuente no guarda la meta).

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `meta_key` | integer | no | PK | Llave sustituta; -1 = sin meta. |
| `maquina_key` | integer | no | FK -> dw.dim_maquina | Maquina de la meta. |
| `referencia_key` | integer | no | FK -> dw.dim_referencia | Referencia de la meta; -1 = general de la maquina (respaldo). |
| `pacas_por_hora` | numeric(8,2) | no |  | Percentil 90 de pacas por hora productiva de ese anio, con minimo de 10 jornadas validas. |
| `vigente_desde` | date | no |  | 1 de enero del anio de la version. |
| `vigente_hasta` | date | si |  | 31 de diciembre; nulo en la version vigente. |
| `es_vigente` | boolean | no |  | Verdadero en la version mas reciente de cada maquina y referencia. |

## `dw.fact_produccion`

Una fila por jornada: maquina, dia, turno, operario y referencia.

**Origen:** `Base De Datos`, filas con pacas u horas trabajadas, despues de eliminar duplicados exactos.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `produccion_id` | bigint | no | PK | Identidad generada por la base. |
| `fecha_key` | integer | no | FK -> dw.dim_fecha | `Fecha` -> aaaammdd. |
| `maquina_key` | integer | no | FK -> dw.dim_maquina | `Maquina` -> dim_maquina. |
| `turno_key` | smallint | no | FK -> dw.dim_turno | `Turno` -> `limpiar.clave_turno`. |
| `referencia_key` | integer | no | FK -> dw.dim_referencia | `Referencia` estandarizada; -1 si es nula. |
| `operario_key` | integer | no | FK -> dw.dim_operario | `Operario` limpio; -1 si es nulo. |
| `meta_key` | integer | no | FK -> dw.dim_meta_velocidad | Meta de la maquina, referencia y anio; si no existe, la general de la maquina. |
| `pacas_producidas` | numeric(10,2) | si |  | `Pacas producidas`; nulo si supera 60 pacas por hora (regla `pacas_atipicas`). |
| `pacas_origen` | numeric(10,2) | si |  | `Pacas producidas` tal como viene en el Excel. |
| `horas_programadas` | numeric(5,2) | no |  | `Horas trabajadas`; nulo -> 0. |
| `horas_paro` | numeric(10,6) | no |  | `Tiempo de Paro` de la propia fila. No incluye las filas de subcodigo (estan en fact_paro). |
| `horas_productivas` | numeric(10,6) (calculada) | si |  | Calculada: max(horas_programadas - horas_paro, 0). |
| `valida_rendimiento` | boolean | no |  | Verdadero si pacas_producidas no es nulo y las horas productivas son mayores que 0. |
| `bandera_calidad` | text | si |  | Reglas que aplican: pacas_atipicas, sin_pacas, sin_horas, cero_pacas, cero_horas, paro_mayor_horas. |
| `fila_origen` | integer | no |  | Numero de fila en la hoja del Excel, para auditar. |

## `dw.fact_paro`

Una fila por evento de paro: jornada o fila de subcodigo, y codigo de paro (con subcodigo si lo tiene).

**Origen:** `Base De Datos`, columnas `Codigo N en horas` (N = 1 a 18) despivotadas; se conserva el evento si las horas son mayores que 0.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `paro_id` | bigint | no | PK | Identidad generada por la base. |
| `fecha_key` | integer | no | FK -> dw.dim_fecha | `Fecha` de la fila. |
| `maquina_key` | integer | no | FK -> dw.dim_maquina | `Maquina` de la fila. |
| `turno_key` | smallint | no | FK -> dw.dim_turno | `Turno` de la fila. |
| `referencia_key` | integer | no | FK -> dw.dim_referencia | `Referencia` de la fila. |
| `operario_key` | integer | no | FK -> dw.dim_operario | `Operario` de la fila. |
| `paro_key` | integer | no | FK -> dw.dim_paro | Codigo N + subcodigo normalizado (`limpiar.normalizar_subcodigo`) -> hoja de dim_paro. |
| `area_key` | smallint | no | FK -> dw.dim_area_involucrada | `Area involucrada en subcodigo 5`, solo para el codigo 5; los demas codigos usan -1. |
| `horas_paro` | numeric(10,6) | no |  | `Codigo N en horas`, sin redondear. |
| `minutos_paro` | numeric(12,4) (calculada) | si |  | Calculada: horas_paro * 60. |
| `eventos` | smallint | no |  | Siempre 1; sirve para contar fallas (MTBF, MTTR). |
| `hoja_origen` | text | no |  | Hoja del Excel de la que sale el evento. |
| `fila_origen` | integer | no |  | Numero de fila en esa hoja. |

## `dw.fact_registro_horario`

Una fila por maquina y hora. Lo alimenta la simulacion para el monitoreo en Grafana.

**Origen:** Script de simulacion (fase de Grafana); sin historico.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `registro_id` | bigint | no | PK | Identidad generada por la base. |
| `fecha_hora` | timestamp | no |  | Inicio de la hora simulada. |
| `fecha_key` | integer | no | FK -> dw.dim_fecha | Dia de `fecha_hora`, en aaaammdd. |
| `hora_key` | smallint | no | FK -> dw.dim_hora | Hora (0 a 23) de `fecha_hora`. |
| `maquina_key` | integer | no | FK -> dw.dim_maquina | Maquina simulada. |
| `turno_key` | smallint | no | FK -> dw.dim_turno | Turno al que pertenece la hora. |
| `referencia_key` | integer | no | FK -> dw.dim_referencia | Referencia que la simulacion asigna a la maquina. |
| `paro_key` | integer | no | FK -> dw.dim_paro | Causa del paro simulado; -1 si la hora no tuvo paro. |
| `meta_key` | integer | no | FK -> dw.dim_meta_velocidad | Meta vigente de la maquina y referencia en esa fecha. |
| `pacas_hora` | numeric(8,2) | no |  | Pacas producidas en la hora. |
| `minutos_paro` | numeric(5,2) | no |  | Minutos de paro dentro de la hora (0 a 60). |

## `seguridad.operario_pii`

Nombre real de cada operario. Acceso restringido; los tableros no lo leen.

**Origen:** `Base De Datos`.`Operario`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `operario_key` | integer | no | FK -> dw.dim_operario | Llave de dim_operario. |
| `nombre_original` | text | no |  | Nombre sin espacios sobrantes. |

## `calidad.incidencias`

Bitacora de correcciones del ETL, una fila por hallazgo.

**Origen:** Generada por `transformar.py`.

| Columna | Tipo | Nulo | Llave | Origen y regla de transformacion |
|---|---|:-:|---|---|
| `incidencia_id` | integer | no | PK | Identidad generada. |
| `hoja_origen` | text | no |  | Hoja del Excel. |
| `fila_origen` | integer | no |  | Fila en esa hoja. |
| `regla` | text | no |  | duplicado_exacto o pacas_atipicas. |
| `accion` | text | no |  | Fila eliminada o valor anulado. |
| `detalle` | text | si |  | Valores afectados. |
