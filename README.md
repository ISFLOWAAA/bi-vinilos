# BI Vinilos y Témperas: producción y paros de las líneas de envasado

Proyecto final de Inteligencia de Negocios. Integra los registros históricos de producción y paros de las
líneas Vinilos_1 a Vinilos_4 en un modelo dimensional (PostgreSQL) y los consume desde:

- **Power BI**: análisis gerencial (tendencias, comparativos, Pareto de causas de paro, OEE).
- **Grafana**: monitoreo casi en tiempo real con alertas para supervisores y mantenimiento.

**Integrantes:** Andrés Felipe Asprilla Pedroza y Jorge Andres grisales _

## Arquitectura

```
Excel (.xlsm) ──► ETL (Python) ──► PostgreSQL (modelo estrella) ──► Power BI (gerencia)
                                           │
                                           └──► Grafana (monitoreo + alertas)
                                   simulacion/ inserta datos hora a hora ──┘
```

_(El diagrama final va en `docs/`)_

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `data/raw/` | Fuente original (Excel) y el procedimiento P-MTO-22 en `docs/` |
| `etl/` | Código de extracción, limpieza, transformación y carga |
| `sql/` | DDL del modelo, índices y consultas analíticas |
| `simulacion/` | Script que inserta registros nuevos hora a hora |
| `grafana/` | Tablero exportado (JSON) y *provisioning* automático |
| `powerbi/` | Proyecto de Power BI en formato PBIP |
| `docs/` | Diagnóstico, diccionario de datos, catálogo de indicadores, capturas |

## Cómo reproducir desde cero

_(Se completa a medida que avanza el proyecto)_

Requisitos: Git, Docker Desktop (en marcha) y Python 3.11 o superior.

1. Clonar el repositorio.
2. Copiar `.env.example` como `.env` y definir las contraseñas (si los puertos 5432 o 3000 ya están ocupados en tu equipo, cambia `POSTGRES_PORT` y `GRAFANA_PORT`).
3. Levantar la base de datos: `docker compose up -d --wait` (crea las tablas y los datos fijos solo la primera vez).
4. Crear el entorno de Python e instalar las librerías:
   `python -m venv .venv` y `.venv\Scripts\python -m pip install -r etl\requirements.txt`
5. Ejecutar el ETL: `.venv\Scripts\python etl\main.py`. Termina con `TODO CUADRA` y escribe [`docs/validacion_etl.md`](docs/validacion_etl.md).
6. Abrir el proyecto de Power BI en `powerbi/` y Grafana en `http://localhost:<GRAFANA_PORT>` _(pendiente)_.

Más detalle del ETL en [`etl/README.md`](etl/README.md).

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/diagnostico/diagnostico_fuente.md`](docs/diagnostico/diagnostico_fuente.md) | Estructura del Excel, problemas de calidad y limitaciones del reporte actual |
| [`docs/catalogo_indicadores.md`](docs/catalogo_indicadores.md) | Usuarios, preguntas de negocio, supuestos e indicadores (incluido el OEE) |
| [`docs/modelo_dimensional.md`](docs/modelo_dimensional.md) | Modelo en estrella, granularidad, jerarquía de paros, matriz de bus |
| [`docs/diccionario_datos.md`](docs/diccionario_datos.md) | Columnas, tipos, llaves, origen y reglas de cada tabla |
| [`docs/validacion_etl.md`](docs/validacion_etl.md) | Reglas de limpieza con conteos antes y después, y cuadre de totales |

## Tecnologías

Python · PostgreSQL · DBeaver · Power BI Desktop · Grafana · Docker · Git/GitHub
