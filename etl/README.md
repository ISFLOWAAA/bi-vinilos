# ETL: del Excel al modelo estrella

El ETL toma el Excel de seguimiento, lo limpia y lo carga en PostgreSQL. Después comprueba que los totales cuadren con el Excel.

## Cómo ejecutarlo (desde la raíz del repositorio)

Lo más simple es `iniciar.ps1` (o `iniciar.sh`), que hace todo esto y más. Paso a paso:

```powershell
docker compose up -d --wait                       # 1. levantar PostgreSQL
python -m venv .venv                              # 2. crear el entorno de Python (solo la primera vez)
.venv\Scripts\python -m pip install -r etl\requirements.txt
.venv\Scripts\python etl\main.py                  # 3. correr el ETL
```

Necesita el archivo `.env` (copiar `.env.example` y poner contraseñas). Se puede ejecutar las veces que se quiera: cada corrida borra lo que cargó la anterior y lo vuelve a cargar, dentro de una transacción (si algo falla, la base queda como estaba).

Al terminar escribe el informe [`docs/validacion_etl.md`](../docs/validacion_etl.md) y muestra `TODO CUADRA` o `HAY DIFERENCIAS SIN EXPLICAR`.

## Qué hace cada archivo

| Archivo | Etapa | Qué hace |
|---|---|---|
| `main.py` | Orquesta | Llama a las cuatro etapas en orden e imprime el resumen. |
| `config.py` | — | Rutas, parámetros de negocio (umbrales) y conexión a la base. |
| `extraer.py` | 1. Extraer | Lee la hoja `Base De Datos` y la tabla de códigos. No cambia ningún dato. |
| `limpiar.py` | 2. Transformar | Reglas de limpieza: turnos, operarios, referencias, subcódigos. Son funciones pequeñas y con pruebas. |
| `transformar.py` | 2. Transformar | Elimina duplicados, arma dimensiones y hechos, despivota los 18 códigos de paro y calcula la velocidad de referencia. |
| `cargar.py` | 3. Cargar | Inserta las tablas en PostgreSQL con `COPY`. |
| `validar.py` | 4. Validar | Cuadra los totales contra el Excel y escribe el informe. |
| `diccionario.py` | Documentación | Genera `docs/diccionario_datos.md` desde la base. Se corre aparte. |
| `tests/test_limpiar.py` | Pruebas | Verifica las reglas de limpieza: `.venv\Scripts\python -m pytest etl\tests`. |

## Por qué Python

- Hay que **despivotar** 18 pares de columnas "código / horas" y **normalizar texto sucio** (subcódigos con dos formatos y erratas, referencias con variantes). Eso es largo y frágil en SQL o Power Query; en pandas son unas pocas líneas con pruebas.
- Es **reproducible** (un comando, sin clics) y queda en Git, a diferencia de un flujo de Power Query dentro de un `.pbix`.
- Se separa del consumo: la misma base sirve a Power BI y a Grafana.

## Reglas de limpieza (resumen)

El detalle con conteos antes y después está en [`docs/validacion_etl.md`](../docs/validacion_etl.md).

| Regla | Qué se hace | Por qué |
|---|---|---|
| Duplicados exactos | Se eliminan 42 filas iguales en las 58 columnas y se anotan en `calidad.incidencias`. | Son copias de un mismo registro. |
| Filas de subcódigo | No se cuentan como jornadas: solo generan eventos de paro. | No tienen producción; contarlas bajaría artificialmente los promedios. |
| Turno | 8 formas de escribirlo pasan a 6 turnos; nulo o `No aplica` pasa a `Sin turno`. | Un catálogo único permite comparar. |
| Operario | `No` y `No aplica` pasan a nulo; cada nombre recibe un código `OP-nnn`; el nombre va a un esquema aparte. | Protección de datos personales. |
| Referencia | Se corrigen erratas (`Alocdor`, `Stilo Kids`) y se unifica el formato. | Evita contar la misma referencia como dos. |
| Subcódigo | Se normalizan los dos formatos; el catálogo antiguo `4.x` del código 05 se convierte al actual `5.x` por nombre. | Permite el drill-down por subsistema. |
| Pacas atípicas | Si una jornada supera 60 pacas por hora, la cifra se anula y se conserva en `pacas_origen`. | Son 11 jornadas de Vinilos_1 (julio de 2023) que parecen unidades digitadas como pacas; inflaban el total en 14 %. |
| Velocidad de referencia | Percentil 90 de pacas por hora productiva, por máquina, referencia y año (mínimo 10 jornadas). | La fuente no guarda la meta; hace falta para calcular el rendimiento del OEE. |
| Hoja oculta de subcódigos | No se carga. | Sus 1.252 filas ya están todas en `Base De Datos`. |

## Parámetros que se pueden cambiar

Están al inicio de `config.py`: el umbral de pacas atípicas (60 por hora), el percentil de la velocidad de referencia (0,90), el mínimo de jornadas (10) y los códigos de paro programados.
