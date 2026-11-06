# Power BI: tablero analítico para la gerencia

Proyecto en formato **PBIP** (carpetas de texto). Se eligió sobre el `.pbix` porque un `.pbix` es un binario: Git no puede mostrar qué cambió entre dos commits ni permite fusionar el trabajo de dos personas. Con PBIP el modelo (TMDL) y las páginas (JSON) son texto y se versionan como código.

## Cómo abrirlo

1. Tener la base levantada y el ETL corrido (ver el [README principal](../README.md)).
2. En Power BI Desktop: **Archivo › Opciones › Características en versión preliminar** y activar *Almacenar el modelo semántico con formato TMDL* y *Almacenar informes con formato mejorado de metadatos (PBIR)*. Reiniciar Power BI.
3. **Archivo › Abrir informe** y elegir `powerbi/BI_Vinilos.pbip`.
4. Power BI pide las credenciales de PostgreSQL: pestaña **Base de datos**, con el usuario de solo lectura (`BI_LECTOR_USER` y `BI_LECTOR_PASSWORD` del `.env`). Si ofrece conexión sin cifrar, aceptar (la base corre en tu propio equipo).
5. **Inicio › Actualizar** para cargar los datos. El proyecto no guarda los datos importados, así que hay que actualizar cada vez que se abre.

Si el puerto de tu `.env` no es 5433: **Transformar datos › Administrar parámetros** y cambiar `Servidor`.

Las credenciales **no se guardan en el repositorio**: Power BI las conserva solo en el equipo.

## Qué contiene

**Conexión:** a la base de datos (esquema `dw`), nunca al Excel. Modo importación. No se cargan `seguridad.operario_pii` ni `calidad`, por lo que ningún nombre real llega al tablero.

**Modelo:** estrella con 2 tablas de hechos (`fact_produccion`, `fact_paro`) y 8 dimensiones, 13 relaciones de uno a muchos. `dim_fecha` está marcada como tabla de fechas.

**Jerarquías:** `Calendario` (año, trimestre, mes, día) y `Jerarquía de paros` (área de impacto, código, subsistema, detalle).

**Medidas DAX** (carpetas dentro de `fact_produccion`):

| Carpeta | Medidas |
|---|---|
| 1. Básicas | Pacas, Horas programadas, Jornadas, Horas de paro, Eventos de paro, Horas productivas, Pacas por hora programada |
| 2. OEE | Disponibilidad, Pacas válidas, Pacas ideales, Rendimiento, Calidad (proxy), **OEE** |
| 3. Paros | Horas paro programado / no programado, % paro no programado, % del paro total, **Pareto % acumulado**, Fallas, MTTR, MTBF |
| 4. Inteligencia de tiempo | Pacas año anterior, Variación vs año anterior (`SAMEPERIODLASTYEAR`), Pacas acumuladas del año (`TOTALYTD`), OEE año anterior, Variación OEE, OEE promedio móvil 3 meses (`DATESINPERIOD`) |

Las fórmulas siguen el catálogo: [`docs/catalogo_indicadores.md`](../docs/catalogo_indicadores.md).

**Páginas:**

| Página | Qué responde |
|---|---|
| Resumen ejecutivo | ¿Cómo va el OEE y cuál máquina rinde menos? Tarjetas, línea mensual por máquina y tabla resumen |
| Paros y causas | ¿Qué causas concentran las horas perdidas? **Pareto**, **drill-down** (área › código › subsistema › detalle), MTTR y MTBF |
| Comparativo anual | ¿Mejoramos frente al mismo mes del año pasado? Líneas por año, matriz máquina × año, rendimiento por turno |

Cada página tiene navegador de páginas y segmentadores (año, máquina, área de impacto). Para bajar por la jerarquía de paros: en el gráfico de barras de "Horas de paro: área › código › subsistema › detalle", activar las flechas de arriba del visual (*Activar modo de profundización*) y hacer clic en una barra.

## Notas

- **Interpretación:** el rendimiento puede superar 100 % (la velocidad de referencia es un percentil 90 histórico) y la calidad es un proxy; ver los supuestos S3 y S4 del catálogo.
- **Comparativo anual:** las tarjetas "año anterior" y "Variación" comparan contra el mismo periodo del año anterior, por lo que **solo tienen sentido con un año seleccionado**. Esa página todavía no tiene segmentador de año (mejora pendiente); mientras tanto, sin año seleccionado muestran el total completo y una variación de 0 %.
- **Edición:** el proyecto lo guardó Power BI Desktop en su formato nativo. Para editar los archivos a mano, cerrar Power BI **sin guardar** antes, o se pisarán los cambios.
- **Si algo no abre:** copiar el mensaje exacto de Power BI; los archivos de texto permiten arreglar solo la pieza afectada (un visual, una tabla) sin rehacer el resto. Ver también [docs/configuracion.md](../docs/configuracion.md).
