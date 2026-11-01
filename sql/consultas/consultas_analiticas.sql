-- =============================================================================
-- Consultas analiticas. Cada una responde una pregunta de negocio.
-- Ejecutar una a una en DBeaver (conexion al contenedor, puerto de POSTGRES_PORT).
-- Requiere haber corrido el ETL. Usa la vista dw.v_oee_mensual (sql/init/03_vistas.sql).
-- =============================================================================


-- Q1. PARETO DE CAUSAS DE PARO  (usuario: direccion y mantenimiento)
-- Pregunta: ¿que pocas causas concentran la mayor parte de las horas perdidas?
-- Tecnica: SUM() OVER () para el total y SUM() OVER (ORDER BY ...) para el % acumulado.
SELECT p.codigo_paro, p.nombre_codigo, p.area_impacto,
       round(sum(f.horas_paro), 1)                                              AS horas,
       round(100 * sum(f.horas_paro) / sum(sum(f.horas_paro)) OVER (), 1)       AS pct,
       round(100 * sum(sum(f.horas_paro)) OVER (ORDER BY sum(f.horas_paro) DESC)
                 / sum(sum(f.horas_paro)) OVER (), 1)                           AS pct_acumulado
FROM dw.fact_paro f
JOIN dw.dim_paro p USING (paro_key)
GROUP BY p.codigo_paro, p.nombre_codigo, p.area_impacto
ORDER BY horas DESC;


-- Q2. OEE MENSUAL POR MAQUINA  (usuario: direccion)
-- Pregunta: ¿como evolucionan disponibilidad, rendimiento, calidad y OEE de cada maquina?
SELECT maquina, anio_mes,
       round(100 * disponibilidad, 1) AS disponibilidad_pct,
       round(100 * rendimiento, 1)    AS rendimiento_pct,
       round(100 * calidad, 1)        AS calidad_pct,
       round(100 * oee, 1)            AS oee_pct
FROM dw.v_oee_mensual
ORDER BY maquina, anio_mes;


-- Q3. COMPARATIVO ANUAL (mismo mes, anio contra anio anterior)  (usuario: direccion)
-- Pregunta: ¿mejoramos frente al mismo mes del anio pasado?
-- Tecnica: LAG() sobre una ventana por maquina y mes, ordenada por anio.
-- Se compara pacas por hora programada para que dias registrados distintos no distorsionen.
WITH mensual AS (
    SELECT maquina, anio, mes, oee, pacas / nullif(horas_programadas, 0) AS pacas_por_hora
    FROM dw.v_oee_mensual
)
SELECT maquina, anio, mes,
       round(pacas_por_hora::numeric, 2)                                        AS pacas_por_hora,
       round(lag(pacas_por_hora) OVER w ::numeric, 2)                           AS mismo_mes_anio_anterior,
       round(100 * (pacas_por_hora - lag(pacas_por_hora) OVER w)
                 / nullif(lag(pacas_por_hora) OVER w, 0)::numeric, 1)           AS variacion_pct,
       round(100 * (oee - lag(oee) OVER w)::numeric, 1)                         AS variacion_oee_puntos
FROM mensual
WINDOW w AS (PARTITION BY maquina, mes ORDER BY anio)
ORDER BY maquina, anio, mes;


-- Q4. RANKING DE MAQUINAS POR MES  (usuario: direccion, planeacion)
-- Pregunta: ¿que maquina rinde mejor y cual peor cada mes?
-- Tecnica: RANK() con PARTITION BY mes.
SELECT anio_mes, maquina, round(100 * oee, 1) AS oee_pct,
       rank() OVER (PARTITION BY anio_mes ORDER BY oee DESC) AS puesto
FROM dw.v_oee_mensual
WHERE oee IS NOT NULL
ORDER BY anio_mes, puesto;


-- Q5. TENDENCIA SUAVIZADA (promedio movil de 3 meses)  (usuario: direccion)
-- Pregunta: ¿la tendencia de fondo del OEE sube o baja, sin el ruido de un mes malo?
-- Tecnica: AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW).
SELECT maquina, anio_mes, round(100 * oee, 1) AS oee_pct,
       round(100 * avg(oee) OVER (PARTITION BY maquina ORDER BY anio_mes
                                   ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS oee_movil_3m_pct
FROM dw.v_oee_mensual
WHERE oee IS NOT NULL
ORDER BY maquina, anio_mes;


-- Q6. MTTR Y MTBF DE FALLAS ELECTROMECANICAS (codigo 01)  (usuario: mantenimiento)
-- Pregunta: ¿cada cuanto falla una maquina y cuanto tarda en repararse?
-- MTTR = horas de falla / numero de fallas.  MTBF = horas productivas / numero de fallas.
WITH fallas AS (
    SELECT f.maquina_key, d.anio, sum(f.horas_paro) AS horas_falla, sum(f.eventos) AS n_fallas
    FROM dw.fact_paro f
    JOIN dw.dim_paro p  USING (paro_key)
    JOIN dw.dim_fecha d USING (fecha_key)
    WHERE p.codigo_paro = 1
    GROUP BY f.maquina_key, d.anio
), horas AS (
    SELECT f.maquina_key, d.anio, sum(f.horas_programadas) AS horas_programadas
    FROM dw.fact_produccion f JOIN dw.dim_fecha d USING (fecha_key)
    GROUP BY f.maquina_key, d.anio
), paro AS (
    SELECT f.maquina_key, d.anio, sum(f.horas_paro) AS horas_paro
    FROM dw.fact_paro f JOIN dw.dim_fecha d USING (fecha_key)
    GROUP BY f.maquina_key, d.anio
)
SELECT m.nombre AS maquina, fa.anio, fa.n_fallas,
       round(fa.horas_falla / fa.n_fallas, 2)                                       AS mttr_horas,
       round((h.horas_programadas - coalesce(p.horas_paro, 0)) / fa.n_fallas, 1)    AS mtbf_horas
FROM fallas fa
JOIN horas h USING (maquina_key, anio)
LEFT JOIN paro p USING (maquina_key, anio)
JOIN dw.dim_maquina m USING (maquina_key)
ORDER BY maquina, anio;


-- Q7. PARO PROGRAMADO FRENTE A NO PROGRAMADO  (usuario: direccion, planeacion)
-- Pregunta: ¿cuanto del tiempo perdido es evitable?
SELECT m.nombre AS maquina, d.anio,
       round(sum(f.horas_paro) FILTER (WHERE p.es_programado), 0)      AS horas_programado,
       round(sum(f.horas_paro) FILTER (WHERE NOT p.es_programado), 0)  AS horas_no_programado,
       round(100 * sum(f.horas_paro) FILTER (WHERE NOT p.es_programado) / sum(f.horas_paro), 1) AS pct_no_programado
FROM dw.fact_paro f
JOIN dw.dim_paro p     USING (paro_key)
JOIN dw.dim_fecha d    USING (fecha_key)
JOIN dw.dim_maquina m  USING (maquina_key)
GROUP BY m.nombre, d.anio
ORDER BY maquina, anio;


-- Q8. DRILL-DOWN DE LA JERARQUIA DE PAROS (codigos 01 y 05)  (usuario: mantenimiento)
-- Pregunta: dentro de las fallas y los ajustes, ¿que subsistema y que detalle pesan mas?
-- Tecnica: ROLLUP entrega codigo, subsistema y detalle con sus subtotales; GROUPING() marca el nivel.
SELECT CASE GROUPING(p.nombre_codigo, p.subsistema_nombre, p.detalle_nombre)
            WHEN 0 THEN '3. detalle' WHEN 1 THEN '2. subsistema' WHEN 3 THEN '1. codigo' ELSE 'total' END AS nivel,
       p.nombre_codigo, p.subsistema_nombre, p.detalle_nombre,
       round(sum(f.horas_paro), 1) AS horas
FROM dw.fact_paro f
JOIN dw.dim_paro p USING (paro_key)
WHERE p.codigo_paro IN (1, 5)
GROUP BY ROLLUP (p.nombre_codigo, p.subsistema_nombre, p.detalle_nombre)
ORDER BY p.nombre_codigo NULLS LAST, p.subsistema_nombre NULLS FIRST, horas DESC;


-- Q9. LOS 3 DIAS CON MAS PARO DE CADA MAQUINA  (usuario: supervisores, mantenimiento)
-- Pregunta: ¿que dias concentran los peores paros para investigar su causa?
-- Tecnica: ROW_NUMBER() por maquina y filtro en una subconsulta.
SELECT maquina, fecha, horas_paro, causa_principal
FROM (
    SELECT m.nombre AS maquina, d.fecha,
           round(sum(f.horas_paro), 1) AS horas_paro,
           (array_agg(p.nombre_codigo ORDER BY f.horas_paro DESC))[1] AS causa_principal,
           row_number() OVER (PARTITION BY m.nombre ORDER BY sum(f.horas_paro) DESC) AS puesto
    FROM dw.fact_paro f
    JOIN dw.dim_paro p     USING (paro_key)
    JOIN dw.dim_fecha d    USING (fecha_key)
    JOIN dw.dim_maquina m  USING (maquina_key)
    GROUP BY m.nombre, d.fecha
) t
WHERE puesto <= 3
ORDER BY maquina, puesto;


-- Q10. RENDIMIENTO POR TURNO  (usuario: supervisores)
-- Pregunta: ¿que turno rinde mas frente a su meta?  Se excluyen jornadas sin turno.
-- Se compara contra la velocidad de referencia (no pacas por hora a secas) porque cada maquina
-- tiene un ritmo distinto y, si no, el turno que mas corre en la maquina rapida siempre gana.
SELECT t.nombre AS turno,
       count(*)                                                                  AS jornadas,
       round(100 * sum(f.pacas_producidas)
                 / sum(f.horas_productivas * mv.pacas_por_hora), 1)              AS rendimiento_pct
FROM dw.fact_produccion f
JOIN dw.dim_turno t            USING (turno_key)
JOIN dw.dim_meta_velocidad mv  USING (meta_key)
WHERE f.valida_rendimiento AND f.turno_key <> -1 AND f.meta_key <> -1
GROUP BY t.nombre
ORDER BY rendimiento_pct DESC;
