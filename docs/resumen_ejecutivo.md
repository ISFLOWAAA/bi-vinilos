# Resumen ejecutivo: hallazgos y recomendaciones

Cifras del modelo cargado, del 2 de enero de 2022 al 28 de marzo de 2025: 5.138 jornadas, 37.934 horas programadas, 8.432 horas de paro y 325.266 pacas válidas.

## El problema

La dirección revisa un informe mensual hecho a mano en Excel. No puede comparar años con facilidad, no sabe qué causas pesan más y los supervisores solo se enteran de un paro cuando ya pasó. Se construyó una solución que integra los datos en un modelo en estrella, con un tablero analítico en Power BI y uno operativo con alerta en Grafana.

## Hallazgos

| # | Hallazgo | Evidencia |
|---|---|---|
| 1 | **El OEE promedio mensual de las líneas está entre 55 % y 64 %**, lejos de la referencia mundial de 85 %. | 2022: 63,8 % · 2023: 55,2 % · 2024: 58,0 % · 2025 (hasta marzo): 56,7 % |
| 2 | **La disponibilidad es la principal pérdida y baja cada año.** | 87,0 % (2022) → 79,8 % → 69,3 % → 67,2 % (2025) |
| 3 | **Vinilos_2 es la línea más débil**, y Vinilos_3 y Vinilos_4 las mejores. | OEE promedio: Vinilos_2 49,4 % · Vinilos_1 53,7 % · Vinilos_3 64,7 % · Vinilos_4 65,2 % |
| 4 | **Cinco causas concentran el 79 % de las horas de paro**, y ninguna es una falla de máquina. | Aseo y alimentación [16] 23,7 % · Ajuste operativo [05] 21,5 % · Derrames [06] 18,3 % · Pausa activa [17] 8,5 % · Cambio de referencia [07] 7,4 % |
| 5 | **Las fallas electromecánicas pesan solo el 3,8 %** del paro (323 h). El problema no es principalmente de mantenimiento correctivo. | MTTR de 0,3 a 0,9 h por falla |
| 6 | **El 66 % del paro (5.540 h) es no programado**, es decir, evitable. | Paro programado: [15], [16], [17], [04], [18] |
| 7 | **Dentro del ajuste operativo, el sistema de dosificación de pintura es el mayor responsable:** 43 % de las horas de ajuste. | 784 de 1.813 h |

### Una advertencia sobre el hallazgo 2

Parte de la caída de disponibilidad puede deberse a que **desde 2023 se registran más paros**, y no solo a un deterioro real. Por ejemplo, el cambio de referencia [07] suma 11 horas en 2022 y 378 en 2024. Antes de concluir que la planta empeoró, hay que confirmar con mantenimiento si la forma de registrar cambió. Lo mismo aplica al rendimiento: la velocidad de referencia se calcula por año, por lo que el rendimiento no es comparable entre años y solo sirve para comparar máquinas dentro del mismo periodo.

## Recomendaciones

| # | Recomendación | Impacto esperado |
|---|---|---|
| 1 | **Atacar los paros no programados de proceso** (ajustes, derrames, cambios de referencia) con un plan de estandarización: procedimientos de ajuste, listas de verificación y cambio rápido de referencia. | Reducir esas causas en 20 % recuperaría unas **1.100 horas, cerca de 3 puntos de disponibilidad** (escenario ilustrativo: 5.540 h × 20 % = 1.108 h sobre 37.934 h) |
| 2 | **Priorizar el sistema de dosificación de pintura** (ajuste y falla): es la causa individual más grande dentro del ajuste operativo y el primer subsistema en fallas. | Concentra 784 h de ajuste y 117 h de falla |
| 3 | **Revisar la línea Vinilos_2** (OEE 49 %, disponibilidad 72 %): el mejor candidato para un piloto de mejora y de medición automática. | Es la línea con más margen de mejora |
| 4 | **Mejorar la captura de datos:** turno obligatorio, guardar la meta por hora, validar la cifra al digitar (pacas contra unidades), registrar producto no conforme. | Hoy 47 % de las jornadas no tienen turno y no se puede medir la calidad real |
| 5 | **Usar el tablero de Grafana en los turnos** y acordar quién responde cuando salta la alerta de paro prolongado. | Pasar de enterarse al final del mes a reaccionar en el turno |
| 6 | **Evolucionar a medición automática** con PLC o SCADA, empezando por un piloto en una línea. | Datos en segundos, sin transcripción manual (ver `evolucion_plc_scada.md`) |

## Limitaciones que el lector debe conocer

- La **velocidad de referencia** es un percentil 90 del histórico y no la velocidad nominal de la máquina; por eso el OEE puede pasar de 100 % en algún mes.
- La **calidad** es una aproximación (horas de reproceso y materia prima defectuosa), porque la fuente no registra producto no conforme.
- Las **11 jornadas con pacas imposibles** (Vinilos_1, julio de 2023) se anularon en el cálculo de rendimiento y quedaron documentadas.
- Los datos de **2025 llegan solo hasta marzo**.
