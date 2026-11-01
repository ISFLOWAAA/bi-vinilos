#!/bin/bash
# Usuario de solo lectura para los tableros (Grafana y Power BI).
# Minimo privilegio: puede leer el esquema dw y nada mas. No ve seguridad (nombres reales
# de operarios) ni calidad, y no puede insertar, modificar ni borrar.
# Se ejecuta una sola vez, al crear la base, con las variables del archivo .env.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE ${BI_LECTOR_USER} LOGIN PASSWORD '${BI_LECTOR_PASSWORD}'
        NOSUPERUSER NOCREATEDB NOCREATEROLE;

    REVOKE ALL ON SCHEMA seguridad, calidad FROM PUBLIC;
    GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO ${BI_LECTOR_USER};
    GRANT USAGE ON SCHEMA dw TO ${BI_LECTOR_USER};
    GRANT SELECT ON ALL TABLES IN SCHEMA dw TO ${BI_LECTOR_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA dw GRANT SELECT ON TABLES TO ${BI_LECTOR_USER};
EOSQL
