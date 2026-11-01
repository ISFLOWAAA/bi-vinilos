# Usuarios, preguntas de negocio y catálogo de indicadores

## 1. Usuarios y preguntas de negocio

| Usuario | Necesidad | Preguntas que debe poder responder | Herramienta |
|---|---|---|---|
| **Alta dirección y jefes de área** | Decidir inversiones y planes de mantenimiento | ¿Cómo evoluciona el OEE por máquina y año? ¿Qué máquina rinde menos? ¿Qué causas concentran el 80 % de las horas perdidas? ¿Mejoramos frente al año anterior? | Power BI |
| **Coordinador de mantenimiento** | Priorizar intervenciones y presentar el informe mensual | ¿Qué fallas (código 01, 03, 05) y qué subcódigos pesan más? ¿Cuánto tarda en promedio una reparación (MTTR) y cada cuánto falla una máquina (MTBF)? ¿Qué parte del paro es evitable? | Power BI y Grafana |
| **Supervisores de producción** | Reaccionar durante el turno | ¿Qué máquinas están paradas ahora? ¿Cuánto llevan paradas? ¿Cómo va la producción del turno frente a la meta? | Grafana |
| **Planeación** | Programar referencias y cambios | ¿Cuánto tiempo se pierde en cambios de referencia (código 07)? ¿Qué referencias rinden menos? | Power BI |

## 2. Supuestos de cálculo (derivados del diagnóstico)

| # | Supuesto | Razón |
|---|---|---|
| S1 | **Horas programadas** = `Horas trabajadas` de la fila con producción (duración del turno registrada). El paro está incluido en ese tiempo. | Solo 45 de 5.160 filas tienen paro mayor que las horas trabajadas. |
| S2 | **Tiempo productivo** = Horas programadas − Horas de paro, donde las horas de paro se suman de `fact_paro` (incluye las filas de subcódigo). | Es la lógica de la hoja `Tiempos` del Excel actual; usar `fact_paro` evita perder el 9,5 % del paro que viene en filas de subcódigo. |
| S3 | **Meta por hora (pacas)** no se guarda en la base: las columnas de velocidad ideal están vacías en el 100 % de las filas. Se define una **velocidad de referencia por máquina y referencia** a partir del histórico (percentil 90 de pacas por hora productiva), almacenada en una tabla propia y editable. | Sin velocidad ideal no se puede calcular Rendimiento. Es la limitación más importante de la fuente. |
| S3b | Como la velocidad de referencia es el **percentil 90** y no un máximo teórico, el rendimiento (y por tanto el OEE) **puede superar 100 %** cuando una jornada o un mes supera su propia referencia (ocurre en pocos casos, p. ej. Vinilos_3 en 2023). En los tableros se muestra tal cual y se interpreta como "mejor que su referencia habitual". | Es una consecuencia de no tener la velocidad ideal del fabricante. |
| S4 | **Calidad no se registra** (no hay producto no conforme). Versión 1: proxy = 1 − (horas de [11] Reproceso + [12] Materia prima defectuosa) / Horas programadas, declarado como aproximación. Se propone capturar unidades no conformes. | Sin ese dato, el componente Calidad del OEE no es medible directamente. |
| S5 | **Paros programados**: los que la hoja `TABLA CODIGOS` clasifica con área de impacto "Paro programado" ([15] Cambio de insumos, [16] Alimentación y aseo, [17] Pausa activa), más [04] Mantenimiento preventivo y [18] Desinfección, que son programados por definición. El resto es no programado. | Permite separar pérdida controlable de pérdida programada, respetando la clasificación de la empresa. |
| S6 | Las filas de subcódigo sin producción **no son jornadas**; solo aportan a paros, y sus horas son **adicionales** (no duplican las de la jornada). | Verificado con los datos; ver `docs/diagnostico/diagnostico_fuente.md`, sección 4. |
| S7 | Las **11 jornadas con pacas imposibles** (más de 60 pacas por hora) conservan sus horas pero no sus pacas, y quedan fuera del cálculo de rendimiento (`valida_rendimiento = false`). | Evita que un error de digitación distorsione el OEE de Vinilos_1 en 2023. |

Los umbrales de esta tabla son **iniciales**: se calibran con el histórico cuando el ETL esté cargado y se confirman con el coordinador de mantenimiento.

## 3. Catálogo de indicadores

Granularidad: la mínima a la que se puede calcular; todos se agregan por máquina, turno, referencia, mes y año.

### 3.1 Indicadores que reporta hoy el P-MTO-22

| ID | Indicador | Fórmula | Unidad | Granularidad | Meta / umbral | Fuente | Usuario |
|---|---|---|---|---|---|---|---|
| I01 | Productividad por máquina y mes | Pacas reales ÷ (velocidad de referencia × Tiempo productivo) | % | Máquina, mes | Meta ≥ 75 %; alerta < 65 % (el reporte actual muestra 76,3 % global) | `fact_produccion` | Dirección |
| I02 | Comparativo anual de producción | Pacas reales del mes del año N frente a las del mismo mes del año N−1 | Pacas y % de variación | Año, mes | Variación ≥ 0 % | `fact_produccion` | Dirección |
| I03 | % de horas por código de paro | Horas del código ÷ Horas programadas | % | Máquina, mes, código | Cada código no planeado < 2 %; ajuste [05], aseo [16] y derrame [06] son los que hoy superan 4 % | `fact_paro` | Mantenimiento |
| I04 | Detalle código 01 (falla electromecánica) por subcódigo | Horas del subcódigo ÷ Horas del código 01 | % | Subcódigo | Informativo; Pareto | `fact_paro`, `dim_paro` | Mantenimiento |
| I05 | Detalle código 03 (sistemas de potencia) por subcódigo | Igual que I04 para el código 03 | % | Subcódigo | Informativo | `fact_paro` | Mantenimiento |
| I06 | Detalle código 05 (ajuste operativo) por subcódigo y personal | Igual que I04 para el código 05, abierto por personal involucrado (operarios o mantenimiento) | % | Subcódigo, personal | Informativo | `fact_paro` | Mantenimiento |

### 3.2 Indicadores nuevos que el Excel no calcula

| ID | Indicador | Fórmula | Unidad | Granularidad | Meta / umbral | Fuente | Usuario |
|---|---|---|---|---|---|---|---|
| I07 | Disponibilidad | Tiempo productivo ÷ Horas programadas | % | Jornada | Meta ≥ 90 %; alerta < 80 % | `fact_produccion`, `fact_paro` | Todos |
| I08 | Rendimiento | Pacas reales ÷ (velocidad de referencia × Tiempo productivo) | % | Jornada | Meta ≥ 95 %; alerta < 80 % | `fact_produccion`, tabla de velocidades | Dirección, producción |
| I09 | Calidad (proxy v1) | 1 − (horas [11] + [12]) ÷ Horas programadas | % | Jornada | Meta ≥ 99 % | `fact_paro` | Dirección |
| I10 | **OEE** | Disponibilidad × Rendimiento × Calidad | % | Jornada, máquina, mes | Meta ≥ 65 % inicial, referencia mundial 85 %; alerta < 50 % | Derivado | Dirección |
| I11 | Pareto de causas de paro | Horas por código ordenadas de mayor a menor y % acumulado | Horas y % | Código, subcódigo | 80 % acumulado define las "pocas causas vitales" | `fact_paro` | Dirección, mantenimiento |
| I12 | MTTR (tiempo medio de reparación) | Horas del código 01 ÷ Número de eventos del código 01 | Horas | Máquina, mes | Tendencia decreciente | `fact_paro` | Mantenimiento |
| I13 | MTBF (tiempo medio entre fallas) | Tiempo productivo ÷ Número de eventos del código 01 | Horas | Máquina, mes | Tendencia creciente | `fact_paro` | Mantenimiento |
| I14 | % de paro planeado frente a no planeado | Horas de paros planeados (S5) ÷ Horas de paro totales | % | Máquina, mes | No planeado < 50 % del paro total | `fact_paro` | Dirección, planeación |
| I15 | Pacas por hora productiva | Pacas reales ÷ Tiempo productivo | Pacas/h | Jornada, referencia | Comparar contra la referencia | `fact_produccion` | Planeación |
| I16 | Tiempo medio de cambio de referencia | Horas del código 07 ÷ Número de cambios | Horas | Máquina, mes | Tendencia decreciente | `fact_paro` | Planeación |
| I17 | Variación mensual de OEE | OEE del mes − OEE del mes anterior | Puntos porcentuales | Máquina, mes | ≥ 0 | Derivado | Dirección |

### 3.3 Indicadores operativos de Grafana (casi en tiempo real)

| ID | Indicador | Fórmula | Unidad | Granularidad | Meta / umbral | Fuente | Usuario |
|---|---|---|---|---|---|---|---|
| I18 | Estado actual por máquina | "Parada" si la última hora registrada tiene paro mayor que 30 min, "Produciendo" en caso contrario | Estado | Máquina, hora | — | Tabla de la simulación | Supervisores |
| I19 | Pacas por hora (serie temporal) | Pacas registradas en la hora | Pacas/h | Máquina, hora | Referencia de la velocidad (S3) | `fact_produccion` | Supervisores |
| I20 | **Horas de paro en la última hora** (KPI de la alerta) | Suma de minutos de paro de la hora ÷ 60 | Horas | Máquina, hora | **Alerta si > 0,5 h (30 min)** durante 2 horas seguidas: equivale a perder más de la mitad de la hora, el punto donde la disponibilidad horaria queda bajo 50 % y justifica llamar a mantenimiento | `fact_paro` | Supervisores, mantenimiento |

## 4. Por qué estos indicadores nuevos

- **OEE (I07–I10):** resume en un número la pérdida de disponibilidad, velocidad y calidad. El Excel solo mide "eficiencia" frente a una meta digitada a mano y sin histórico.
- **Pareto (I11):** el gráfico actual muestra porcentajes por código, pero no el acumulado que permite priorizar.
- **MTTR y MTBF (I12, I13):** separan cuántas veces falla una máquina de cuánto tarda en repararse, dos decisiones de inversión distintas.
- **Planeado vs no planeado (I14):** evita corregir como "falla" lo que es una parada programada.
- **Tiempo de cambio de referencia (I16):** el código 07 acumula 620,8 h en la fuente; medirlo por cambio orienta la programación.
- **Indicadores horarios (I18–I20):** el reporte mensual llega demasiado tarde para actuar en el turno.
