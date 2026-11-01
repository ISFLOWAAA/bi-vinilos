-- =============================================================================
-- DDL del modelo dimensional (estrella) - BI Vinilos y Temperas
-- Motor: PostgreSQL 16. Se ejecuta automaticamente al crear el contenedor.
-- Diseno y justificacion: docs/modelo_dimensional.md
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS dw;          -- modelo analitico (lo consumen Power BI y Grafana)
CREATE SCHEMA IF NOT EXISTS seguridad;   -- datos personales, fuera del alcance de los tableros
CREATE SCHEMA IF NOT EXISTS calidad;     -- bitacora de incidencias detectadas por el ETL

-- -----------------------------------------------------------------------------
-- DIMENSIONES
-- -----------------------------------------------------------------------------

-- Calendario construido por nosotros (no viene del Excel). Llave inteligente aaaammdd.
CREATE TABLE dw.dim_fecha (
    fecha_key      integer     PRIMARY KEY,
    fecha          date        NOT NULL UNIQUE,
    anio           smallint    NOT NULL,
    trimestre      smallint    NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    mes            smallint    NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre_mes     text        NOT NULL,
    semana_iso     smallint    NOT NULL,
    dia            smallint    NOT NULL CHECK (dia BETWEEN 1 AND 31),
    dia_semana     smallint    NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    nombre_dia     text        NOT NULL,
    es_fin_semana  boolean     NOT NULL,
    anio_mes       char(7)     NOT NULL
);

-- Horas del dia para el monitoreo hora a hora.
CREATE TABLE dw.dim_hora (
    hora_key  smallint  PRIMARY KEY CHECK (hora_key BETWEEN 0 AND 23),
    franja    text      NOT NULL
);

CREATE TABLE dw.dim_maquina (
    maquina_key     integer  PRIMARY KEY,
    nombre          text     NOT NULL UNIQUE,
    linea_producto  text     NOT NULL
);

-- Catalogo limpio de turnos (8 valores crudos del Excel -> 6 turnos + "Sin turno").
CREATE TABLE dw.dim_turno (
    turno_key        smallint      PRIMARY KEY,
    nombre           text          NOT NULL UNIQUE,
    tipo_turno       text          NOT NULL,
    hora_inicio      time,
    hora_fin         time,
    duracion_horas   numeric(4,1)  CHECK (duracion_horas > 0)
);

CREATE TABLE dw.dim_referencia (
    referencia_key   integer   PRIMARY KEY,
    nombre_estandar  text      NOT NULL UNIQUE,   -- nombre ya corregido (erratas y formato unificados)
    producto         text      NOT NULL,
    contenido_cc     smallint  CHECK (contenido_cc > 0),
    num_colores      smallint  CHECK (num_colores > 0)
);

-- El nombre real NO vive aqui: solo un codigo seudonimo (ver seguridad.operario_pii).
CREATE TABLE dw.dim_operario (
    operario_key       integer  PRIMARY KEY,
    codigo_seudonimo   text     NOT NULL UNIQUE,
    activo             boolean  NOT NULL DEFAULT true
);

CREATE TABLE seguridad.operario_pii (
    operario_key     integer  PRIMARY KEY REFERENCES dw.dim_operario (operario_key),
    nombre_original  text     NOT NULL
);

-- Jerarquia de paros desnormalizada: area -> codigo -> subsistema -> detalle.
-- Una fila por hoja de la jerarquia; los niveles que no aplican usan 'Sin subcodigo'.
CREATE TABLE dw.dim_paro (
    paro_key           integer   PRIMARY KEY,
    area_impacto       text      NOT NULL,
    codigo_paro        smallint  NOT NULL CHECK (codigo_paro BETWEEN 0 AND 19),
    nombre_codigo      text      NOT NULL,
    es_programado      boolean   NOT NULL,
    subsistema_codigo  text      NOT NULL DEFAULT 'Sin subcodigo',
    subsistema_nombre  text      NOT NULL DEFAULT 'Sin subcodigo',
    detalle_codigo     text      NOT NULL DEFAULT 'Sin subcodigo',
    detalle_nombre     text      NOT NULL DEFAULT 'Sin subcodigo',
    UNIQUE (codigo_paro, subsistema_codigo, detalle_codigo)
);

CREATE TABLE dw.dim_area_involucrada (
    area_key  smallint  PRIMARY KEY,
    nombre    text      NOT NULL UNIQUE
);

-- SCD tipo 2: la velocidad de referencia cambia con el tiempo y se conserva la historia.
CREATE TABLE dw.dim_meta_velocidad (
    meta_key         integer       PRIMARY KEY,
    maquina_key      integer       NOT NULL REFERENCES dw.dim_maquina (maquina_key),
    referencia_key   integer       NOT NULL REFERENCES dw.dim_referencia (referencia_key),
    pacas_por_hora   numeric(8,2)  NOT NULL CHECK (pacas_por_hora > 0),
    vigente_desde    date          NOT NULL,
    vigente_hasta    date,
    es_vigente       boolean       NOT NULL DEFAULT true,
    CHECK (vigente_hasta IS NULL OR vigente_hasta >= vigente_desde),
    UNIQUE (maquina_key, referencia_key, vigente_desde)
);

-- -----------------------------------------------------------------------------
-- HECHOS
-- -----------------------------------------------------------------------------

-- Grano: una jornada (maquina, dia, turno, operario, referencia).
CREATE TABLE dw.fact_produccion (
    produccion_id       bigint        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_key           integer       NOT NULL REFERENCES dw.dim_fecha (fecha_key),
    maquina_key         integer       NOT NULL REFERENCES dw.dim_maquina (maquina_key),
    turno_key           smallint      NOT NULL REFERENCES dw.dim_turno (turno_key),
    referencia_key      integer       NOT NULL REFERENCES dw.dim_referencia (referencia_key),
    operario_key        integer       NOT NULL REFERENCES dw.dim_operario (operario_key),
    meta_key            integer       NOT NULL REFERENCES dw.dim_meta_velocidad (meta_key),
    pacas_producidas    numeric(10,2) CHECK (pacas_producidas >= 0),   -- NULL si el valor de origen es atipico
    pacas_origen        numeric(10,2),                                 -- valor tal como viene en el Excel
    horas_programadas   numeric(5,2)  NOT NULL CHECK (horas_programadas >= 0),
    -- Paro registrado en la propia fila. Los subcodigos adicionales viven en fact_paro.
    horas_paro          numeric(10,6) NOT NULL DEFAULT 0 CHECK (horas_paro >= 0),
    horas_productivas   numeric(10,6) GENERATED ALWAYS AS (GREATEST(horas_programadas - horas_paro, 0)) STORED,
    valida_rendimiento  boolean       NOT NULL,    -- true si hay pacas validas y horas productivas > 0
    bandera_calidad     text,                      -- reglas de calidad que aplican, separadas por coma
    fila_origen         integer       NOT NULL UNIQUE   -- fila de Excel, para auditar
);

-- Grano: un evento de paro (jornada + codigo de paro [+ subcodigo]) con horas > 0.
CREATE TABLE dw.fact_paro (
    paro_id          bigint        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_key        integer       NOT NULL REFERENCES dw.dim_fecha (fecha_key),
    maquina_key      integer       NOT NULL REFERENCES dw.dim_maquina (maquina_key),
    turno_key        smallint      NOT NULL REFERENCES dw.dim_turno (turno_key),
    referencia_key   integer       NOT NULL REFERENCES dw.dim_referencia (referencia_key),
    operario_key     integer       NOT NULL REFERENCES dw.dim_operario (operario_key),
    paro_key         integer       NOT NULL REFERENCES dw.dim_paro (paro_key),
    area_key         smallint      NOT NULL REFERENCES dw.dim_area_involucrada (area_key),
    horas_paro       numeric(10,6) NOT NULL CHECK (horas_paro > 0),
    minutos_paro     numeric(12,4) GENERATED ALWAYS AS (horas_paro * 60) STORED,
    eventos          smallint      NOT NULL DEFAULT 1 CHECK (eventos = 1),
    hoja_origen      text          NOT NULL,
    fila_origen      integer       NOT NULL
);

-- Grano: una hora de una maquina. Lo alimenta la simulacion y lo lee Grafana.
CREATE TABLE dw.fact_registro_horario (
    registro_id      bigint        GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_hora       timestamp     NOT NULL,
    fecha_key        integer       NOT NULL REFERENCES dw.dim_fecha (fecha_key),
    hora_key         smallint      NOT NULL REFERENCES dw.dim_hora (hora_key),
    maquina_key      integer       NOT NULL REFERENCES dw.dim_maquina (maquina_key),
    turno_key        smallint      NOT NULL REFERENCES dw.dim_turno (turno_key),
    referencia_key   integer       NOT NULL REFERENCES dw.dim_referencia (referencia_key),
    paro_key         integer       NOT NULL REFERENCES dw.dim_paro (paro_key),
    meta_key         integer       NOT NULL REFERENCES dw.dim_meta_velocidad (meta_key),
    pacas_hora       numeric(8,2)  NOT NULL CHECK (pacas_hora >= 0),
    minutos_paro     numeric(5,2)  NOT NULL DEFAULT 0 CHECK (minutos_paro BETWEEN 0 AND 60),
    UNIQUE (maquina_key, fecha_hora)   -- una lectura por maquina y hora; evita duplicar la simulacion
);

-- -----------------------------------------------------------------------------
-- CALIDAD DE DATOS: cada correccion relevante del ETL deja una fila aqui.
-- -----------------------------------------------------------------------------
CREATE TABLE calidad.incidencias (
    incidencia_id  integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    hoja_origen    text    NOT NULL,
    fila_origen    integer NOT NULL,
    regla          text    NOT NULL,   -- ej. duplicado_exacto, pacas_atipicas
    accion         text    NOT NULL,   -- ej. fila eliminada, valor anulado
    detalle        text
);

-- -----------------------------------------------------------------------------
-- INDICES (consultas tipicas: por maquina y periodo, por causa de paro, series de tiempo)
-- Las PK y UNIQUE ya crean su propio indice.
-- -----------------------------------------------------------------------------

-- Tendencias y comparativos: filtrar por maquina y ordenar/agrupar por fecha.
CREATE INDEX ix_fprod_maquina_fecha  ON dw.fact_produccion (maquina_key, fecha_key);
CREATE INDEX ix_fprod_fecha          ON dw.fact_produccion (fecha_key);
CREATE INDEX ix_fprod_referencia     ON dw.fact_produccion (referencia_key);
CREATE INDEX ix_fprod_turno          ON dw.fact_produccion (turno_key);

-- Pareto y drill-down: agrupar horas por causa, y por causa dentro de una maquina.
CREATE INDEX ix_fparo_paro           ON dw.fact_paro (paro_key);
CREATE INDEX ix_fparo_maquina_fecha  ON dw.fact_paro (maquina_key, fecha_key);
CREATE INDEX ix_fparo_fecha          ON dw.fact_paro (fecha_key);
CREATE INDEX ix_fparo_operario       ON dw.fact_paro (operario_key);

-- Grafana: ultimas horas por maquina; el filtro casi siempre es una ventana reciente.
CREATE INDEX ix_freg_fechahora       ON dw.fact_registro_horario (fecha_hora DESC);

-- Metas vigentes: busqueda por maquina y referencia.
CREATE INDEX ix_meta_vigente         ON dw.dim_meta_velocidad (maquina_key, referencia_key) WHERE es_vigente;
