# Scripts SQL

Todo el SQL del proyecto, en dos carpetas con funciones distintas.

## `init/`: se ejecuta solo, una vez

Estos archivos crean la base al levantar Docker por primera vez. PostgreSQL los ejecuta **en orden alfabético y solo si la base está vacía**:

| Orden | Archivo | Qué hace |
|---|---|---|
| 1 | `01_ddl.sql` | Crea los esquemas (`dw`, `seguridad`, `calidad`), las 9 dimensiones, las 3 tablas de hechos, las restricciones y los índices |
| 2 | `02_seed.sql` | Carga los datos fijos: calendario 2022–2030, horas, turnos y el miembro "Desconocido" de cada dimensión |
| 3 | `03_vistas.sql` | Crea la vista `dw.v_oee_mensual` con el OEE y sus componentes por máquina y mes |
| 4 | `04_roles.sh` | Crea el usuario de solo lectura que usan Grafana y Power BI |

Las tablas quedan vacías hasta que se ejecuta el ETL (`python etl/main.py`), que carga el Excel.

> **Si cambias algo en `init/`**, hay que recrear la base: `docker compose down -v` y volver a levantar, porque estos archivos no se vuelven a ejecutar con la base ya creada. Ver [docs/configuracion.md](../docs/configuracion.md).

## `consultas/`: se ejecuta a mano

[`consultas_analiticas.sql`](consultas/consultas_analiticas.sql) tiene **10 consultas**, cada una con la pregunta de negocio que responde y la técnica que usa (agregaciones, funciones de ventana, comparativos entre periodos):

| Consulta | Pregunta |
|---|---|
| Q1 | ¿Qué pocas causas concentran las horas perdidas? (Pareto) |
| Q2 | ¿Cómo evolucionan disponibilidad, rendimiento, calidad y OEE por máquina? |
| Q3 | ¿Mejoramos frente al mismo mes del año anterior? |
| Q4 | ¿Qué máquina rinde mejor y cuál peor cada mes? |
| Q5 | ¿Cuál es la tendencia de fondo sin el ruido de un mes? |
| Q6 | ¿Cada cuánto falla una máquina y cuánto tarda en repararse? |
| Q7 | ¿Cuánto del paro es evitable? |
| Q8 | Dentro de fallas y ajustes, ¿qué subsistema y detalle pesan más? |
| Q9 | ¿Qué días concentran los peores paros? |
| Q10 | ¿Qué turno rinde más frente a su meta? |

### Cómo ejecutarlas

- **En DBeaver:** abrir el archivo, seleccionar una consulta y pulsar Ctrl + Enter. Datos de conexión en [docs/configuracion.md](../docs/configuracion.md).
- **Desde la terminal** (una consulta de ejemplo):

  ```
  docker exec -it bi_vinilos_postgres psql -U <usuario> -d <base> -c "SELECT * FROM dw.v_oee_mensual LIMIT 5"
  ```

Las tablas y columnas están explicadas en el [diccionario de datos](../docs/diccionario_datos.md), y las restricciones e índices en [docs/base_de_datos.md](../docs/base_de_datos.md).
