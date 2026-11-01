# Diagnóstico de la fuente de datos

Fuente: `data/raw/SEGUIMIENTO_TEMPERAS_Y_VINILOS_Actividad.xlsm` (4,2 MB, 21 hojas) y procedimiento `P-MTO-22`.
Todas las cifras salen de leer el archivo sin modificarlo.

## 1. Estructura del libro

| Hoja | Estado | Contenido | Uso en el proyecto |
|---|---|---|---|
| `Base De Datos` | visible | 8.208 registros × 58 columnas (encabezado en la fila 9) | **Fuente principal** de hechos |
| `Base de datos de Sub codigos` | oculta | 1.260 filas × 19 columnas | Detalle de subcódigos, área y personal involucrado |
| `TABLA CODIGOS` | oculta | Área de impacto, códigos de paro y jerarquía de subcódigos | **Fuente de la dimensión de paros** |
| `Registro`, `Tiempos` | visible | Formulario de captura (botones con macros) y cálculo de tiempos | Se documenta, no se carga |
| `TD_*`, `prod*`, `ajusteOperativo`, `fallaMecanica`, `novPotencia` | visible | Tablas dinámicas y gráficos del informe actual | Referencia de los indicadores actuales |
| `Calculadora de tiempos`, `Hoja1`, `Hoja4`, `Tablas Desplegables` | oculta/visible | Apoyo | No se cargan |

Cada fila de `Base De Datos` es una **jornada de una máquina con un operario, una referencia y un turno**. Cubre del **2022-01-01 al 2025-03-28**:

| Año | Registros |
|---|---|
| 2022 | 1.654 |
| 2023 | 2.891 |
| 2024 | 3.129 |
| 2025 (parcial) | 534 |

Máquinas: Vinilos_1 (1.877), Vinilos_2 (1.255), Vinilos_3 (2.491), Vinilos_4 (2.585). Operarios distintos: 34. Referencias distintas: 52.

## 2. Qué está bien

- Las 8.208 fechas son válidas y la columna `Año` coincide con el año de `Fecha` en todas las filas.
- **`Tiempo de Paro` es igual a la suma de las 18 columnas "Código N en horas" en el 100 % de las filas.** Sirve como control de cuadre del ETL.
- No hay valores negativos en pacas, horas trabajadas ni tiempo de paro.

## 3. Problemas de calidad de datos

| # | Problema | Evidencia | Tratamiento propuesto en el ETL |
|---|---|---|---|
| 1 | **Paros en formato ancho**: 18 pares "Código N" / "Código N en horas" por fila | 58 columnas | Despivotar a una fila por (jornada, código de paro) con horas > 0 |
| 2 | **Turno inconsistente** | 8 valores: `6am-2pm (Turno 1)` 1.352, `2pm-10pm (Turno 2)` 1.182, `10pm-6am (Turno 3)` 1.012, `6am-4:30pm` 359, `No aplica` 336, `6am-6pm` 35, `6pm-6am` 20, nulo 3.912 | Catálogo único de turnos; nulo o `No aplica` pasa a "Sin turno" y se reporta el conteo |
| 3 | **Dos catálogos de "Tipo de paro" mezclados** | Esquema antiguo (`17. PARO DE MAQUINA` 952, `9.FALTA DE PROGRAMACIÓN` 251, …) y esquema nuevo (`[19] No aplica` 2.282, `[18] Paro de maquina por ventas` 605, …); 3.782 nulos | Tabla de equivalencias antiguo → nuevo, documentada |
| 4 | **Filas de subcódigo sin producción** | 3.048 filas (37 %) sin pacas ni horas trabajadas; 3.047 tienen un subcódigo. Suman 799,2 h de paro (9,5 % de 8.449,7 h). 2.120 tienen una fila "padre" con producción en la misma fecha, máquina y turno | No cuentan como jornadas: alimentan solo la tabla de hechos de paros |
| 5 | **Operario y referencia nulos** | Operario nulo 3.721 y `No aplica` 537; referencia nula 3.874 | Miembro "Desconocido" en la dimensión; se reporta el conteo |
| 6 | **Duplicados** | 42 duplicados exactos; 5.377 filas comparten (fecha, máquina, operario, referencia, turno) | Eliminar los exactos; los demás son legítimos (varias referencias o subcódigos en una jornada) y se conservan |
| 7 | **Valores atípicos** | Pacas: máximo 9.417 con media 73,45 | Marcar con bandera de calidad y revisar caso por caso |
| 8 | **Ceros** | 427 filas con pacas = 0 y 401 con horas trabajadas = 0 | Mantener, con bandera para no inflar promedios |
| 9 | **Código 18 sin documentar** | El PDF lista 17 códigos; el Excel y los gráficos usan 18 (`Desinfección`) y el tipo `[19] No aplica` | Se agrega a la dimensión de paros |
| 10 | **Datos personales** | 34 nombres de operarios en texto claro | Seudonimizar en el modelo (ver sección de seguridad) |
| 11 | **Archivo con macros** | `.xlsm`; las hojas `Registro` y `Tiempos` dependen de VBA | El ETL lee solo valores (`data_only`) y no ejecuta macros |

## 4. Punto que estaba abierto: las filas de subcódigo (resuelto)

Las filas de subcódigo traen sus propias horas de paro. Se verificó con los datos que **son horas adicionales y no doble conteo**:

- Son casi todas del código 05 (723,3 h), más el 01 (60,0 h) y el 03 (15,8 h).
- Solo la mitad se puede ligar a una jornada con seguridad (1.470 de 3.048 tienen una jornada única con la misma fecha, máquina, operario y referencia), y en esas el código 05 aparece en la jornada solo 280 veces frente a 1.229 en la fila de subcódigo.
- La hoja oculta `Base de datos de Sub codigos` (1.252 filas) está contenida por completo en `Base De Datos`, así que no aporta datos nuevos.

Regla aplicada: las filas de subcódigo no son jornadas y se cargan como **eventos de paro propios** (sus horas se suman al total). Por eso la disponibilidad se calcula con las horas de `fact_paro`, no con la columna `horas_paro` de `fact_produccion`.

## 5. Hallazgos adicionales al cargar los datos

| Hallazgo | Detalle |
|---|---|
| Pacas imposibles | 11 jornadas de Vinilos_1 en julio de 2023 con entre 3.552 y 9.417 pacas en 8 h (unas 500 por hora, cuando lo normal son 7). Suman 52.493 pacas, el 14 % del total. Parecen unidades digitadas como pacas. |
| Subcódigos con dos catálogos | En el código 05 conviven la numeración antigua `4.x` y la actual `5.x`, y no coinciden (el antiguo 4.4 Transfer es hoy el 5.5). |
| Meta no guardada | Las columnas de velocidad ideal (unidades por minuto, unidades por display, displays por paca) están vacías en el 100 % de las filas. |
| Código 1.1 con dos nombres | El catálogo lo llama "Falla mecánica"; los datos y los gráficos del P-MTO-22 usan "Sistema alimentador de envases". |

## 6. Limitaciones del esquema actual de reporte

## 6. Limitaciones del esquema actual de reporte

1. **No calcula OEE** ni sus componentes (disponibilidad, rendimiento, calidad).
2. **Cobertura parcial en 2025**: el comparativo 2024 vs 2025 llega solo hasta marzo/abril.
3. **Jerarquía de paros oculta**: la relación código → subcódigo vive en una hoja oculta y se analiza solo para los códigos 01, 03 y 05.
4. **Captura manual**: papel → transcripción → Excel con macros; los errores de digitación (problemas 5, 7 y 8) no se validan al ingresar.
5. **Sin tiempo casi real**: el análisis es mensual y los supervisores no reciben alertas.
6. **Modelo ancho y sin llaves**: no hay identificador de registro; cualquier cruce depende de combinaciones de texto.
7. **Sin trazabilidad de calidad**: no se registra producto no conforme, lo que impide medir el componente "Calidad" del OEE.
