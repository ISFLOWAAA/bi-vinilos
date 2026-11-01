# Configuración y solución de problemas

Este documento reúne todo lo que hay que saber para configurar y operar el proyecto. **No contiene contraseñas**: esas viven solo en el archivo `.env` de cada equipo, que no se sube a Git.

## 1. Requisitos y versiones

| Herramienta | Versión usada | Para qué |
|---|---|---|
| Git | 2.x | Clonar y versionar |
| Docker Desktop | 29.x (en Windows requiere WSL 2) | Levanta PostgreSQL y Grafana |
| Python | 3.11 o superior (se usó 3.14) | ETL y simulación |
| Power BI Desktop | Cualquier versión reciente | Tablero analítico (opcional para correr la base y Grafana) |
| DBeaver | Cualquiera | Administrar y consultar la base (opcional) |
| Google Chrome | Reciente | Solo para regenerar el PDF y las capturas (opcional) |

Imágenes de Docker: `postgres:16` y `grafana/grafana:11.2.0`. Librerías de Python: ver `etl/requirements.txt`.

## 2. Variables del archivo `.env`

El `.env` se crea copiando `.env.example` (el script `iniciar.ps1` o `iniciar.sh` lo hace solo, con contraseñas aleatorias).

| Variable | Qué es | Valor del ejemplo | Notas |
|---|---|---|---|
| `POSTGRES_DB` | Nombre de la base de datos | `bi_vinilos` | |
| `POSTGRES_USER` | Usuario administrador de la base | `bi_user` | Lo usan el ETL y la simulación. Tiene todos los permisos |
| `POSTGRES_PASSWORD` | Contraseña del administrador | `cambia_esta_clave` | **Cámbiala** |
| `POSTGRES_PORT` | Puerto de PostgreSQL **en tu equipo** | `5432` | Si está ocupado (por otro PostgreSQL), usa `5433` |
| `BI_LECTOR_USER` | Usuario de solo lectura para los tableros | `bi_lector` | Solo ve el esquema `dw` |
| `BI_LECTOR_PASSWORD` | Contraseña del usuario de solo lectura | `cambia_esta_clave` | **Cámbiala**. Evita comillas y caracteres especiales |
| `GF_SECURITY_ADMIN_USER` | Usuario administrador de Grafana | `admin` | |
| `GF_SECURITY_ADMIN_PASSWORD` | Contraseña de Grafana | `cambia_esta_clave` | **Cámbiala** |
| `GRAFANA_PORT` | Puerto de Grafana **en tu equipo** | `3000` | Si está ocupado (por otro Grafana), usa `3001` |

Opcional: `POSTGRES_HOST` (por defecto `localhost`), solo si la base está en otra máquina.

## 3. Servicios, puertos y volúmenes

| Servicio | Contenedor | Puerto en tu equipo → contenedor | Datos persistentes |
|---|---|---|---|
| PostgreSQL 16 | `bi_vinilos_postgres` | `POSTGRES_PORT` → 5432 | Volumen `pgdata` |
| Grafana 11.2.0 | `bi_vinilos_grafana` | `GRAFANA_PORT` → 3000 | Volumen `grafana-data` |

```
docker compose up -d --wait     # levantar
docker compose ps               # ver estado
docker compose logs -f grafana  # ver registros
docker compose down             # apagar (conserva los datos)
docker compose down -v          # apagar y BORRAR los datos (vuelve a crear todo la próxima vez)
```

Al crear la base por primera vez se ejecutan, en orden, los archivos de `sql/init/`: `01_ddl.sql` (tablas), `02_seed.sql` (calendario, horas, turnos), `03_vistas.sql` (vista del OEE) y `04_roles.sh` (usuario de solo lectura). **Solo se ejecutan con la base vacía.**

## 4. Usuarios y permisos

| Usuario | Quién lo usa | Permisos |
|---|---|---|
| `POSTGRES_USER` (administrador) | ETL, simulación, DBeaver | Todos |
| `BI_LECTOR_USER` | Grafana (siempre) y Power BI (recomendado) | Solo `SELECT` sobre el esquema `dw`; sin acceso a `seguridad` ni `calidad` |
| `GF_SECURITY_ADMIN_USER` | Entrar a Grafana | Administrador de Grafana |

Detalle y justificación: [seguridad_datos_personales.md](seguridad_datos_personales.md).

## 5. Cómo conectarse

| Herramienta | Parámetros |
|---|---|
| **DBeaver** | Nueva conexión → PostgreSQL. Host `localhost`, puerto `POSTGRES_PORT`, base `POSTGRES_DB`, usuario y contraseña del administrador. Los datos están en el esquema `dw` |
| **Power BI** | Parámetros del modelo `Servidor` (`localhost:<POSTGRES_PORT>`) y `BaseDatos` (`bi_vinilos`). Al abrir pide credenciales: pestaña **Base de datos**, con el usuario de solo lectura |
| **Grafana → PostgreSQL** | Automático: la fuente de datos `BI Vinilos (PostgreSQL)` se crea sola y usa el usuario de solo lectura |
| **Línea de comandos** | `docker exec -it bi_vinilos_postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>` |

## 6. Parámetros que se pueden ajustar

| Dónde | Parámetro | Valor | Efecto |
|---|---|---|---|
| `etl/config.py` | `UMBRAL_PACAS_POR_HORA_ATIPICO` | 60 | Jornadas con más pacas por hora se consideran error de digitación y su cifra se anula |
| `etl/config.py` | `PERCENTIL_VELOCIDAD_REFERENCIA` | 0,90 | Percentil del histórico que define la velocidad de referencia |
| `etl/config.py` | `MIN_OBSERVACIONES_META` | 10 | Mínimo de jornadas para calcular una velocidad de referencia |
| `etl/config.py` | `CODIGOS_PROGRAMADOS_ADICIONALES` | {4, 18} | Códigos de paro programado además de los que marca el Excel |
| `simulacion/simular.py` | `PROB_PARO`, `MINUTOS_FALLA` | 0,20 · 42 a 58 | Frecuencia de paros y duración de la falla provocada |
| `grafana/provisioning/alerting/alertas.yml` | Umbral `30` y `HAVING count(*) = 2` | 30 min · 2 lecturas | Cuándo salta la alerta |

## 7. Hora y zona horaria

- Las lecturas de la simulación se guardan en **UTC** (lo que Grafana espera de una columna `timestamp`); `fecha_key` y `hora_key` usan la hora de Colombia (UTC−5), sin horario de verano.
- El tablero de Grafana usa la zona horaria del navegador.

## 8. Qué NO se sube a Git

| Archivo o carpeta | Por qué |
|---|---|
| `.env` | Contiene contraseñas |
| `.venv/` | Entorno de Python (se recrea con `iniciar.ps1` o `iniciar.sh`) |
| `privado/` | Hoja personal con credenciales y configuración del equipo |
| `simulacion/falla.flag` | Bandera temporal de la demostración |
| `*.pbix`, caché de Power BI | Binarios y datos importados |

## 9. Cambiar una contraseña

Las contraseñas de la base y de Grafana **se aplican solo al crear el volumen por primera vez**. Cambiar el `.env` después no las modifica.

| Quieres cambiar | Cómo |
|---|---|
| Todas (lo más simple, pierde los datos) | Edita `.env`, ejecuta `docker compose down -v`, luego `iniciar.ps1` (recarga todo con el ETL) |
| Solo la de la base, sin perder datos | `docker exec -it bi_vinilos_postgres psql -U <admin> -d <base> -c "ALTER ROLE <usuario> PASSWORD 'nueva';"` y actualiza el `.env` |
| Solo la de Grafana, sin perder datos | `docker exec -it bi_vinilos_grafana grafana cli admin reset-admin-password <nueva>` y actualiza el `.env` |

Después de cambiar la contraseña del usuario de solo lectura, Grafana necesita `docker compose up -d --force-recreate grafana` y Power BI pedirá las credenciales otra vez.

## 10. Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| Docker Desktop se queda en "Starting the Docker Engine" | WSL 2 no está instalado o falta reiniciar | Como administrador: `wsl --install --no-distribution`, reiniciar el equipo y abrir Docker Desktop |
| `failed to connect to the docker API` | Docker Desktop no está abierto | Abrirlo y esperar a "Engine running" |
| `port is already allocated` o la base no arranca | El puerto ya lo usa otro programa (por ejemplo, un PostgreSQL o Grafana instalados en Windows) | Cambia `POSTGRES_PORT` o `GRAFANA_PORT` en el `.env`; `iniciar.ps1` lo detecta solo al crear el `.env` |
| `failed to copy` / `no such host` al descargar imágenes | Falla de red momentánea | Repetir `docker compose pull` |
| `Se encontraron problemas... TMDL` al abrir Power BI | Opciones de vista previa apagadas | Activar *TMDL* y *PBIR* en Archivo → Opciones → Características en versión preliminar y reiniciar |
| Power BI abre pero los visuales están vacíos | Los datos importados no se guardan en el proyecto | Inicio → Actualizar |
| Power BI no se puede conectar | Puerto o credenciales distintos | Revisar el parámetro `Servidor` y usar el usuario de solo lectura de tu `.env` |
| Grafana sin datos | El ETL o la simulación no se han ejecutado | `iniciar.ps1` y luego `simular.py` |
| La alerta de Grafana queda en `Error` | La consulta no marca la máquina como etiqueta | Ya está resuelto: la columna se llama `maquina` en `alertas.yml` |
| `permission denied for schema seguridad` | Es lo esperado con el usuario de solo lectura | Usar el administrador para tareas de mantenimiento |
| `iniciar.ps1` bloqueado por Windows | Política de ejecución de PowerShell | `powershell -ExecutionPolicy Bypass -File .\iniciar.ps1` |
| El ETL dice `HAY DIFERENCIAS SIN EXPLICAR` | Cambió el Excel o una regla | Revisar `docs/validacion_etl.md`: indica qué medida no cuadra |
| Archivos bloqueados al editar | La carpeta está en OneDrive y se está sincronizando | Esperar a que termine o mover el proyecto fuera de OneDrive |
