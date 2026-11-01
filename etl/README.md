# ETL: del Excel al modelo estrella

El ETL toma el Excel de seguimiento, lo limpia y lo carga en PostgreSQL. Despues comprueba que los totales cuadren con el Excel.

## Como ejecutarlo (desde la raiz del repositorio)

```powershell
docker compose up -d --wait                       # 1. levantar PostgreSQL
python -m venv .venv                              # 2. crear el entorno de Python (solo la primera vez)
.venv\Scripts\python -m pip install -r etl\requirements.txt
.venv\Scripts\python etl\main.py                  # 3. correr el ETL
```

Necesita el archivo `.env` (copiar `.env.example` y poner contrasenas). Se puede ejecutar las veces que se quiera: cada corrida borra lo que cargo la anterior y lo vuelve a cargar, dentro de una transaccion (si algo falla, la base queda como estaba).

Al terminar escribe el informe [`docs/validacion_etl.md`](../docs/validacion_etl.md) y muestra `TODO CUADRA` o `HAY DIFERENCIAS SIN EXPLICAR`.

## Que hace cada archivo

| Archivo | Etapa | Que hace |
|---|---|---|
| `main.py` | Orquesta | Llama a las cuatro etapas en orden e imprime el resumen. |
| `config.py` | — | Rutas, parametros de negocio (umbrales) y conexion a la base. |
| `extraer.py` | 1. Extraer | Lee la hoja `Base De Datos` y la tabla de codigos. No cambia ningun dato. |
| `limpiar.py` | 2. Transformar | Reglas de limpieza: turnos, operarios, referencias, subcodigos. Son funciones pequenas y con pruebas. |
| `transformar.py` | 2. Transformar | Elimina duplicados, arma dimensiones y hechos, despivota los 18 codigos de paro y calcula la velocidad de referencia. |
| `cargar.py` | 3. Cargar | Inserta las tablas en PostgreSQL con `COPY`. |
| `validar.py` | 4. Validar | Cuadra los totales contra el Excel y escribe el informe. |
| `diccionario.py` | Documentacion | Genera `docs/diccionario_datos.md` desde la base. Se corre aparte. |
| `tests/test_limpiar.py` | Pruebas | Verifica las reglas de limpieza: `.venv\Scripts\python -m pytest etl\tests`. |

## Por que Python

- Hay que **despivotar** 18 pares de columnas "codigo / horas" y **normalizar texto sucio** (subcodigos con dos formatos y erratas, referencias con variantes). Eso es largo y fragil en SQL o Power Query; en pandas son unas pocas lineas con pruebas.
- Es **reproducible** (un comando, sin clics) y queda en Git, a diferencia de un flujo de Power Query dentro de un `.pbix`.
- Se separa del consumo: la misma base sirve a Power BI y a Grafana.

## Reglas de limpieza (resumen)

El detalle con conteos antes y despues esta en [`docs/validacion_etl.md`](../docs/validacion_etl.md).

| Regla | Que se hace | Por que |
|---|---|---|
| Duplicados exactos | Se eliminan 42 filas iguales en las 58 columnas y se anotan en `calidad.incidencias`. | Son copias de un mismo registro. |
| Filas de subcodigo | No se cuentan como jornadas: solo generan eventos de paro. | No tienen produccion; contarlas bajaria artificialmente los promedios. |
| Turno | 8 formas de escribirlo pasan a 6 turnos; nulo o `No aplica` pasa a `Sin turno`. | Un catalogo unico permite comparar. |
| Operario | `No` y `No aplica` pasan a nulo; cada nombre recibe un codigo `OP-nnn`; el nombre va a un esquema aparte. | Proteccion de datos personales. |
| Referencia | Se corrigen erratas (`Alocdor`, `Stilo Kids`) y se unifica el formato. | Evita contar la misma referencia como dos. |
| Subcodigo | Se normalizan los dos formatos; el catalogo antiguo `4.x` del codigo 05 se convierte al actual `5.x` por nombre. | Permite el drill-down por subsistema. |
| Pacas atipicas | Si una jornada supera 60 pacas por hora, la cifra se anula y se conserva en `pacas_origen`. | Son 11 jornadas de Vinilos_1 (julio de 2023) que parecen unidades digitadas como pacas; inflaban el total en 14 %. |
| Velocidad de referencia | Percentil 90 de pacas por hora productiva, por maquina, referencia y anio (minimo 10 jornadas). | La fuente no guarda la meta; hace falta para calcular el rendimiento del OEE. |
| Hoja oculta de subcodigos | No se carga. | Sus 1.252 filas ya estan todas en `Base De Datos`. |

## Parametros que se pueden cambiar

Estan al inicio de `config.py`: el umbral de pacas atipicas (60 por hora), el percentil de la velocidad de referencia (0,90), el minimo de jornadas (10) y los codigos de paro programados.
