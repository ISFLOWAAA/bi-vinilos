# Power BI y Grafana: para qué sirve cada uno

Las dos herramientas leen el mismo modelo en PostgreSQL, pero responden preguntas distintas para personas distintas. No son intercambiables.

## Comparativo

| | **Power BI** (capa analítica) | **Grafana** (capa operativa) |
|---|---|---|
| **Pregunta que resuelve** | ¿Cómo evolucionó la eficiencia, qué máquina rinde menos y qué causas explican las pérdidas? ¿Mejoramos frente al año anterior? | ¿Qué máquina está parada **ahora**, desde cuándo y por qué? ¿Debo llamar a mantenimiento? |
| **Usuario** | Alta dirección, jefes de área, coordinador de mantenimiento | Supervisores de producción y técnicos de mantenimiento |
| **Decisión que apoya** | Estratégica: inversiones, planes de mantenimiento, programación | Inmediata: reaccionar durante el turno |
| **Horizonte de datos** | Meses y años (2022 a 2025) | Últimos minutos y horas |
| **Frecuencia de actualización** | Por demanda o programada (diaria o mensual), con la actualización del modelo importado | Cada 5 segundos; la alerta se evalúa cada 10 segundos |
| **Granularidad** | Jornada, mes, año; resumen por máquina, turno y referencia | Una lectura por máquina y por hora |
| **Fortaleza** | Modelo semántico, medidas DAX, inteligencia de tiempo, drill-down por la jerarquía de paros, narrativa para el comité | Series de tiempo, estado actual, alertas por umbral, variables de filtro, tablero siempre encendido |
| **Indicadores** | OEE, disponibilidad, rendimiento, calidad, Pareto, MTTR, MTBF, variación anual | Estado por máquina, pacas por hora, minutos de paro, disponibilidad del periodo |
| **Dónde está en el repositorio** | `powerbi/` (formato PBIP) | `grafana/` (JSON y provisioning) |

## Por qué no se intercambian

- **Power BI no sirve para vigilar la planta.** Su modelo es importado: se ve la foto del último refresco, no el presente, y no tiene un motor de alertas continuo. Una alerta de paro que llegara con el informe mensual llega demasiado tarde.
- **Grafana no sirve para el comité de dirección.** No tiene un modelo semántico con medidas como "mismo periodo del año anterior" ni jerarquías de navegación, y está pensado para series recientes, no para comparar años ni contar una historia.
- **Se complementan:** Grafana avisa que una máquina lleva dos lecturas seguidas con más de 30 minutos de paro; Power BI explica, con tres años de historia, qué causas son las que más pesan y si el problema es nuevo o recurrente.

## Qué comparten

El mismo modelo estrella, las mismas definiciones de indicadores (`docs/catalogo_indicadores.md`) y la misma base de datos. Por eso la disponibilidad de una máquina en Grafana y en Power BI se calcula igual.
