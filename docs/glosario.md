# Glosario

Términos que aparecen en el proyecto, explicados sin jerga.

## De la planta

| Término | Qué significa |
|---|---|
| **Línea / máquina** | Cada una de las cuatro máquinas de envasado: Vinilos_1 a Vinilos_4. |
| **Referencia** | El producto que se está envasando, por ejemplo "Parchesitos 22cc (6 col)": nombre, contenido en cc y número de colores. |
| **Paca** | La unidad de producción que se registra en el formato "hora a hora": un paquete de producto terminado. |
| **Jornada** | Un turno de trabajo de una máquina, con un operario y una referencia. Es la unidad básica de producción en la base. |
| **Turno** | Franja de trabajo: turno 1 (6 a 14 h), turno 2 (14 a 22 h), turno 3 (22 a 6 h) y variantes de 10,5 y 12 horas. |
| **Paro** | Tiempo en que la máquina no produce. Se registra con un **código de paro** (del 01 al 18). |
| **Código de paro** | Causa del paro, por ejemplo [05] Ajuste operativo o [16] Alimentación y aseo. La lista está en el procedimiento P-MTO-22. |
| **Subcódigo** | Detalle de la causa dentro de un código, por ejemplo "1.2.B Ajuste de sensor" dentro de [01] Falla electromecánica. |
| **Paro programado** | Parada prevista: mantenimiento preventivo [04], cambio de insumos [15], aseo [16], pausa activa [17] y desinfección [18]. El resto es **no programado** (evitable). |
| **P-MTO-22** | Procedimiento de la empresa para registrar los paros de producción. |

## Indicadores

| Término | Qué significa | Cómo se calcula |
|---|---|---|
| **OEE** | Eficiencia global: qué parte del tiempo y del ritmo ideal se aprovecha bien. | Disponibilidad × Rendimiento × Calidad |
| **Disponibilidad** | Cuánto del tiempo programado la máquina estuvo disponible. | 1 − horas de paro ÷ horas programadas |
| **Rendimiento** | Qué tan cerca de su ritmo habitual produce. | Pacas reales ÷ (velocidad de referencia × horas productivas) |
| **Calidad (proxy)** | Aproximación de la calidad, porque la fuente no registra producto no conforme. | 1 − horas de reproceso y materia prima defectuosa ÷ horas programadas |
| **Velocidad de referencia** | Pacas por hora que se considera normal para una máquina y referencia. Como el Excel no la guarda, se calcula del histórico (percentil 90). | Percentil 90 de las pacas por hora productiva |
| **Pareto** | Ordenar las causas de la que más a la que menos horas pierde y acumular el porcentaje; pocas causas explican casi todo. | Horas por causa y % acumulado |
| **MTTR** | Tiempo medio de reparación: cuánto tarda en arreglarse una falla. | Horas de falla ÷ número de fallas |
| **MTBF** | Tiempo medio entre fallas: cada cuánto falla una máquina. | Horas productivas ÷ número de fallas |

## De datos y modelo

| Término | Qué significa |
|---|---|
| **ETL** | Extraer, transformar y cargar: leer el Excel, limpiarlo y guardarlo en la base. |
| **Modelo dimensional / esquema en estrella** | Forma de organizar los datos para analizarlos: tablas de hechos (lo que se mide) rodeadas de dimensiones (por qué ejes se mira). |
| **Tabla de hechos** | Tabla con las mediciones: producción por jornada, horas de cada paro, lecturas por hora. |
| **Dimensión** | Tabla con los ejes de análisis: fecha, máquina, turno, referencia, operario, causa de paro. |
| **Grano** | Qué representa exactamente una fila de una tabla de hechos (por ejemplo, "una jornada"). |
| **Jerarquía** | Niveles dentro de una dimensión por los que se puede subir y bajar: Año › Trimestre › Mes › Día, o Área › Código › Subsistema › Detalle. |
| **Llave sustituta** | Número que identifica cada fila de una dimensión, creado por nosotros, en lugar de usar el texto original. |
| **Miembro "Desconocido"** | Fila especial (llave −1) que recibe los datos faltantes del Excel para no perder registros. |
| **SCD tipo 2** | Dimensión de cambio lento que conserva el historial: cada cambio crea una versión nueva con su fecha de vigencia. |
| **Seudonimización** | Reemplazar el nombre de una persona por un código (OP-001) y guardar el nombre real aparte. |
| **Duplicado exacto** | Fila idéntica a otra en todas sus columnas; el ETL la elimina y la registra. |

## De herramientas

| Término | Qué significa |
|---|---|
| **PostgreSQL** | La base de datos donde vive el modelo. |
| **Docker / Docker Compose** | Programa que ejecuta PostgreSQL y Grafana en "contenedores" aislados, con un solo comando. |
| **Volumen** | Espacio donde Docker guarda los datos para que no se pierdan al apagar los contenedores. |
| **Power BI** | Herramienta de análisis para la gerencia: tendencias, comparativos y causas. |
| **PBIP** | Formato de proyecto de Power BI en carpetas de texto, que Git puede comparar (a diferencia del archivo `.pbix`). |
| **DAX** | Lenguaje de las fórmulas (medidas) de Power BI. |
| **TMDL** | Formato de texto del modelo semántico de Power BI. |
| **Grafana** | Herramienta de monitoreo casi en tiempo real, con paneles y alertas. |
| **Provisioning** | Configuración de Grafana (fuente de datos, tablero, alerta) que se carga sola desde archivos al iniciar. |
| **Alerta** | Regla que avisa cuando un indicador se sale de su rango; aquí, 2 lecturas seguidas con más de 30 minutos de paro. |
| **DBeaver** | Programa para explorar y consultar la base de datos. |
| **UTC** | Hora universal; las lecturas simuladas se guardan en UTC y Colombia está en UTC−5. |
| **`.env`** | Archivo local con las contraseñas y puertos. Nunca se sube a GitHub. |
