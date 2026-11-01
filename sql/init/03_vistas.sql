-- =============================================================================
-- Vistas de apoyo. Calculan los indicadores a partir de los hechos; no guardan datos.
-- Definicion de cada indicador: docs/catalogo_indicadores.md
-- =============================================================================

-- OEE mensual por maquina (indicadores I07 a I10), como fracciones de 0 a 1.
--   Disponibilidad = 1 - horas de paro (fact_paro, con subcodigos) / horas programadas
--   Rendimiento    = pacas reales / (velocidad de referencia x horas productivas), solo jornadas validas
--   Calidad (proxy)= 1 - horas de reproceso [11] y materia prima defectuosa [12] / horas programadas
CREATE OR REPLACE VIEW dw.v_oee_mensual AS
WITH produccion AS (
    SELECT f.maquina_key, d.anio, d.mes, d.anio_mes,
           sum(f.horas_programadas) AS horas_programadas,
           sum(f.pacas_producidas)                         FILTER (WHERE f.valida_rendimiento) AS pacas,
           sum(f.horas_productivas * mv.pacas_por_hora)    FILTER (WHERE f.valida_rendimiento) AS pacas_ideales
    FROM dw.fact_produccion f
    JOIN dw.dim_fecha d            USING (fecha_key)
    JOIN dw.dim_meta_velocidad mv  USING (meta_key)
    WHERE f.meta_key <> -1
    GROUP BY f.maquina_key, d.anio, d.mes, d.anio_mes
), paro AS (
    SELECT f.maquina_key, d.anio_mes,
           sum(f.horas_paro)                                         AS horas_paro,
           sum(f.horas_paro) FILTER (WHERE p.codigo_paro IN (11, 12)) AS horas_calidad
    FROM dw.fact_paro f
    JOIN dw.dim_fecha d USING (fecha_key)
    JOIN dw.dim_paro p  USING (paro_key)
    GROUP BY f.maquina_key, d.anio_mes
)
SELECT m.nombre AS maquina, p.anio, p.mes, p.anio_mes,
       p.horas_programadas,
       coalesce(a.horas_paro, 0)                                                   AS horas_paro,
       p.pacas, p.pacas_ideales,
       greatest(1 - coalesce(a.horas_paro, 0) / p.horas_programadas, 0)            AS disponibilidad,
       p.pacas / nullif(p.pacas_ideales, 0)                                        AS rendimiento,
       greatest(1 - coalesce(a.horas_calidad, 0) / p.horas_programadas, 0)         AS calidad,
       greatest(1 - coalesce(a.horas_paro, 0) / p.horas_programadas, 0)
         * (p.pacas / nullif(p.pacas_ideales, 0))
         * greatest(1 - coalesce(a.horas_calidad, 0) / p.horas_programadas, 0)     AS oee
FROM produccion p
JOIN dw.dim_maquina m USING (maquina_key)
LEFT JOIN paro a      USING (maquina_key, anio_mes)
WHERE p.horas_programadas > 0;
