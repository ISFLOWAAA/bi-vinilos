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

1. Clonar el repositorio.
2. Copiar `.env.example` como `.env` y definir las credenciales.
3. Levantar los servicios: `docker compose up -d`
4. Ejecutar el ETL: `python etl/main.py`
5. Abrir el proyecto de Power BI en `powerbi/` y Grafana en `http://localhost:3000`.

## Tecnologías

Python · PostgreSQL · DBeaver · Power BI Desktop · Grafana · Docker · Git/GitHub
