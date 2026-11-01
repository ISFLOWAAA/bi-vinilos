# Base de datos: DDL, restricciones, índices y consultas

Motor: **PostgreSQL 16**, administrado desde **DBeaver** (conexión al contenedor, puerto `POSTGRES_PORT`). El DDL completo está en [`sql/init/01_ddl.sql`](../sql/init/01_ddl.sql) y se ejecuta solo al crear el contenedor, junto con los datos fijos (`02_seed.sql`), las vistas (`03_vistas.sql`) y el usuario de solo lectura (`04_roles.sh`).

## Esquemas

| Esquema | Contenido |
|---|---|
| `dw` | Modelo estrella: 9 dimensiones y 3 tablas de hechos. Lo que consumen Power BI y Grafana |
| `seguridad` | Nombres reales de los operarios; acceso restringido |
| `calidad` | Bitácora de correcciones del ETL (`incidencias`) |

## Restricciones y por qué

| Restricción | Dónde | Qué protege |
|---|---|---|
| **Llave primaria** | Todas las tablas | Una fila, una identidad; permite que las uniones sean exactas |
| **Llaves foráneas** | Cada llave de dimensión en los hechos | Imposible cargar un hecho con una máquina, fecha o causa que no existe |
| **Miembro "Desconocido" (llave −1)** | Cada dimensión | Los nulos de la fuente (3.912 turnos, 4.236 operarios) no hacen perder filas en una unión |
| **`NOT NULL`** | Llaves y medidas obligatorias | Evita hechos incompletos |
| **`CHECK` de rango** | Horas ≥ 0, `trimestre` 1 a 4, `hora_key` 0 a 23, `minutos_paro` 0 a 60, `horas_paro` > 0 | Rechaza valores imposibles en la propia base |
| **`UNIQUE`** | Nombres de dimensiones, `fact_produccion.fila_origen`, `fact_registro_horario (maquina_key, fecha_hora)` | Evita duplicados; la simulación no puede insertar dos lecturas de la misma máquina en el mismo instante |
| **Columnas calculadas** (`GENERATED ... STORED`) | `horas_productivas`, `minutos_paro` | El cálculo vive en un solo lugar y no se puede desincronizar |
| **Rango de fechas de vigencia** | `dim_meta_velocidad`: `vigente_hasta ≥ vigente_desde` | Mantiene la coherencia de la dimensión de cambio lento |
| **Mínimo privilegio** | Usuario `bi_lector` | Los tableros leen, no escriben (ver [seguridad](seguridad_datos_personales.md)) |

## Índices y por qué

Las llaves primarias y las restricciones `UNIQUE` ya crean su propio índice. Los demás se definieron según las consultas analíticas más frecuentes:

| Índice | Tabla y columnas | Consulta que acelera |
|---|---|---|
| `ix_fprod_maquina_fecha` | `fact_produccion (maquina_key, fecha_key)` | Tendencias y comparativos: filtrar una máquina y agrupar por fecha (OEE mensual, año contra año) |
| `ix_fprod_fecha` | `fact_produccion (fecha_key)` | Totales por periodo sin filtrar máquina |
| `ix_fprod_referencia`, `ix_fprod_turno` | `fact_produccion` | Cortes por referencia y por turno |
| `ix_fparo_paro` | `fact_paro (paro_key)` | **Pareto** y drill-down: agrupar horas por causa |
| `ix_fparo_maquina_fecha` | `fact_paro (maquina_key, fecha_key)` | Paro de una máquina en un periodo (disponibilidad, MTBF, MTTR) |
| `ix_fparo_fecha`, `ix_fparo_operario` | `fact_paro` | Cortes por fecha y por operario seudonimizado |
| `ix_freg_fechahora` | `fact_registro_horario (fecha_hora DESC)` | Grafana: las lecturas más recientes; casi todos sus filtros son una ventana de tiempo |
| `ix_meta_vigente` (parcial) | `dim_meta_velocidad (maquina_key, referencia_key) WHERE es_vigente` | Buscar la meta vigente de una máquina y referencia; solo indexa las filas vigentes |

No se crearon índices sobre cada columna: cada índice extra hace más lenta la carga del ETL y ocupa espacio. Con unas 5.000 jornadas y 16.000 eventos de paro, estos bastan.

## Consultas analíticas

Las 10 consultas están en [`sql/consultas/consultas_analiticas.sql`](../sql/consultas/consultas_analiticas.sql). Cada una responde una pregunta de negocio y usa agregaciones, funciones de ventana o comparativos entre periodos:

| # | Pregunta de negocio | Técnica |
|---|---|---|
| Q1 | ¿Qué pocas causas concentran las horas perdidas? (Pareto) | `SUM() OVER ()` y acumulado con `SUM() OVER (ORDER BY ...)` |
| Q2 | ¿Cómo evolucionan disponibilidad, rendimiento, calidad y OEE por máquina? | Vista `v_oee_mensual` |
| Q3 | ¿Mejoramos frente al mismo mes del año anterior? | `LAG() OVER (PARTITION BY maquina, mes ORDER BY anio)` |
| Q4 | ¿Qué máquina rinde mejor y cuál peor cada mes? | `RANK() OVER (PARTITION BY mes ...)` |
| Q5 | ¿Cuál es la tendencia de fondo sin el ruido de un mes? | Promedio móvil `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` |
| Q6 | ¿Cada cuánto falla una máquina y cuánto tarda en repararse? | MTTR y MTBF con CTE |
| Q7 | ¿Cuánto del paro es evitable? | `FILTER` sobre paro programado y no programado |
| Q8 | Dentro de fallas y ajustes, ¿qué subsistema y detalle pesan más? | `ROLLUP` con `GROUPING()` |
| Q9 | ¿Qué días concentran los peores paros? | `ROW_NUMBER()` por máquina |
| Q10 | ¿Qué turno rinde más frente a su meta? | Rendimiento contra la velocidad de referencia |
