#!/usr/bin/env bash
# Levanta todo el proyecto con un comando (Linux, macOS o Git Bash):   ./iniciar.sh
#
#  1. Verifica Docker y Python.
#  2. Crea el archivo .env si no existe, con contraseñas aleatorias (nunca se sube a Git).
#  3. Levanta PostgreSQL y Grafana con Docker Compose.
#  4. Prepara el entorno de Python.
#  5. Ejecuta el ETL (carga el Excel al modelo estrella y valida los totales).
#
# Se puede ejecutar varias veces: no duplica datos.
set -euo pipefail
cd "$(dirname "$0")"

paso()   { printf '\n>> %s\n' "$1"; }
fallar() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
clave()  { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20; }
puerto_ocupado() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
puerto_libre()   { if puerto_ocupado "$1"; then echo "$2"; else echo "$1"; fi; }

paso "1/5 Verificando herramientas"
for c in git docker python3; do command -v "$c" >/dev/null || fallar "Falta '$c'. Ver la sección Requisitos del README."; done
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || fallar "Se necesita Python 3.11 o superior."
docker info >/dev/null 2>&1 || fallar "Docker no está en marcha. Inícialo y vuelve a intentar."
echo "   Git, Docker y Python disponibles."

paso "2/5 Archivo .env"
if [ -f .env ]; then
  echo "   Ya existe .env: se conserva tal cual."
else
  sed -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(clave)|" \
      -e "s|^GF_SECURITY_ADMIN_PASSWORD=.*|GF_SECURITY_ADMIN_PASSWORD=$(clave)|" \
      -e "s|^BI_LECTOR_PASSWORD=.*|BI_LECTOR_PASSWORD=$(clave)|" \
      -e "s|^POSTGRES_PORT=.*|POSTGRES_PORT=$(puerto_libre 5432 5433)|" \
      -e "s|^GRAFANA_PORT=.*|GRAFANA_PORT=$(puerto_libre 3000 3001)|" \
      .env.example > .env
  echo "   .env creado con contraseñas aleatorias (no se sube a Git). Revísalo para conocer usuarios, contraseñas y puertos."
fi

paso "3/5 Levantando PostgreSQL y Grafana (la primera vez descarga las imágenes)"
docker compose up -d --wait || fallar "Docker Compose no pudo levantar los servicios. Ver 'docker compose logs'."

paso "4/5 Entorno de Python"
[ -d .venv ] || python3 -m venv .venv
if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=.venv/Scripts/python.exe; fi
"$PY" -m pip install -q -r etl/requirements.txt || fallar "No se pudieron instalar las librerías de Python."
echo "   Librerías instaladas."

paso "5/5 Ejecutando el ETL"
PYTHONIOENCODING=utf-8 "$PY" etl/main.py || fallar "El ETL terminó con diferencias. Ver docs/validacion_etl.md."

valor() { grep -E "^$1=" .env | head -1 | cut -d= -f2-; }
printf '\n=== LISTO ===\n'
echo "Grafana    : http://localhost:$(valor GRAFANA_PORT)   (usuario $(valor GF_SECURITY_ADMIN_USER); la contraseña está en .env)"
echo "PostgreSQL : localhost:$(valor POSTGRES_PORT), base $(valor POSTGRES_DB), usuario de solo lectura $(valor BI_LECTOR_USER)"
echo "Datos en movimiento : $PY simulacion/simular.py"
echo "Power BI            : abrir powerbi/BI_Vinilos.pbip (ver powerbi/README.md)"
