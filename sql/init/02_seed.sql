-- =============================================================================
-- Datos fijos de las dimensiones construidas por nosotros y miembros "Desconocido".
-- Las dimensiones que vienen del Excel (maquina, referencia, operario, paro, meta)
-- las carga el ETL; aqui solo se crea su miembro -1.
-- =============================================================================

-- dim_fecha: calendario 2022-2030 generado (cubre la fuente y la simulacion).
INSERT INTO dw.dim_fecha
SELECT to_char(d, 'YYYYMMDD')::int,
       d::date,
       extract(year    FROM d)::smallint,
       extract(quarter FROM d)::smallint,
       extract(month   FROM d)::smallint,
       (ARRAY['enero','febrero','marzo','abril','mayo','junio','julio','agosto',
              'septiembre','octubre','noviembre','diciembre'])[extract(month FROM d)::int],
       extract(week    FROM d)::smallint,
       extract(day     FROM d)::smallint,
       extract(isodow  FROM d)::smallint,
       (ARRAY['lunes','martes','miercoles','jueves','viernes','sabado','domingo'])[extract(isodow FROM d)::int],
       extract(isodow  FROM d) >= 6,
       to_char(d, 'YYYY-MM')
FROM generate_series('2022-01-01'::date, '2030-12-31'::date, interval '1 day') AS d;

-- dim_hora: 24 horas con su franja.
INSERT INTO dw.dim_hora (hora_key, franja)
SELECT h,
       CASE WHEN h < 6 THEN 'madrugada' WHEN h < 12 THEN 'manana'
            WHEN h < 18 THEN 'tarde'    ELSE 'noche' END
FROM generate_series(0, 23) AS h;

-- dim_turno: catalogo limpio (el -1 recibe los nulos y "No aplica").
INSERT INTO dw.dim_turno (turno_key, nombre, tipo_turno, hora_inicio, hora_fin, duracion_horas) VALUES
    (-1, 'Sin turno',              'Desconocido',        NULL,    NULL,    NULL),
    ( 1, 'Turno 1',                'Turno de 8 h',       '06:00', '14:00', 8),
    ( 2, 'Turno 2',                'Turno de 8 h',       '14:00', '22:00', 8),
    ( 3, 'Turno 3',                'Turno de 8 h',       '22:00', '06:00', 8),
    ( 4, 'Jornada extendida dia',  'Jornada extendida',  '06:00', '16:30', 10.5),
    ( 5, 'Turno 12 h dia',         'Turno de 12 h',      '06:00', '18:00', 12),
    ( 6, 'Turno 12 h noche',       'Turno de 12 h',      '18:00', '06:00', 12);

INSERT INTO dw.dim_area_involucrada (area_key, nombre) VALUES
    (-1, 'No especificado'),
    ( 1, 'Operarios'),
    ( 2, 'Personal de mantenimiento');

-- Miembros "Desconocido" para que ningun hecho se pierda por un nulo de la fuente.
INSERT INTO dw.dim_maquina    (maquina_key, nombre, linea_producto)        VALUES (-1, 'Desconocida', 'Desconocida');
INSERT INTO dw.dim_referencia (referencia_key, nombre_original, producto)  VALUES (-1, 'Desconocida', 'Desconocida');
INSERT INTO dw.dim_operario   (operario_key, codigo_seudonimo, activo)     VALUES (-1, 'OP-DESCONOCIDO', false);
INSERT INTO dw.dim_paro (paro_key, area_impacto, codigo_paro, nombre_codigo, es_programado)
                                                                           VALUES (-1, 'Sin paro', 0, 'Sin paro', false);
INSERT INTO dw.dim_meta_velocidad (meta_key, maquina_key, referencia_key, pacas_por_hora, vigente_desde, es_vigente)
                                                                           VALUES (-1, -1, -1, 1, '2022-01-01', false);
