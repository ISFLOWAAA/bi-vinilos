# Power BI: tablero analitico para la gerencia

Proyecto en formato **PBIP** (carpetas de texto). Se eligio sobre el `.pbix` porque un `.pbix` es un binario: Git no puede mostrar que cambio entre dos commits ni permite fusionar el trabajo de dos personas. Con PBIP el modelo (TMDL) y las paginas (JSON) son texto y se versionan como codigo.

## Como abrirlo

1. Tener la base levantada y el ETL corrido (ver el README principal).
2. En Power BI Desktop: **Archivo > Opciones > Caracteristicas en version preliminar** y activar
   *Almacenar el modelo semantico con formato TMDL* y *Almacenar informes con formato mejorado de metadatos (PBIR)*. Reiniciar Power BI.
3. **Archivo > Abrir informe** y elegir `powerbi/BI_Vinilos.pbip`.
4. Power BI pide las credenciales de PostgreSQL: pestana **Base de datos**, usuario y contrasena del `.env`. Si ofrece conexion sin cifrar, aceptar (la base corre en tu propio equipo).
5. **Actualizar** para cargar los datos. Si el puerto de tu `.env` no es 5433: **Transformar datos > Administrar parametros** y cambiar `Servidor`.

Las credenciales **no se guardan en el repositorio**: Power BI las conserva solo en el equipo.

## Que contiene

**Conexion:** a la base de datos (esquema `dw`), nunca al Excel. Modo importacion. No se cargan `seguridad.operario_pii` ni `calidad`, por lo que ningun nombre real llega al tablero.

**Modelo:** estrella con 2 tablas de hechos (`fact_produccion`, `fact_paro`) y 8 dimensiones, 13 relaciones de uno a muchos. `dim_fecha` esta marcada como tabla de fechas.

**Jerarquias:** `Calendario` (anio, trimestre, mes, dia) y `Jerarquia de paros` (area de impacto, codigo, subsistema, detalle).

**Medidas DAX** (carpetas dentro de `fact_produccion`):

| Carpeta | Medidas |
|---|---|
| 1. Basicas | Pacas, Horas programadas, Jornadas, Horas de paro, Eventos de paro, Horas productivas, Pacas por hora programada |
| 2. OEE | Disponibilidad, Pacas validas, Pacas ideales, Rendimiento, Calidad (proxy), **OEE** |
| 3. Paros | Horas paro programado / no programado, % paro no programado, % del paro total, **Pareto % acumulado**, Fallas, MTTR, MTBF |
| 4. Inteligencia de tiempo | Pacas anio anterior, Variacion vs anio anterior (`SAMEPERIODLASTYEAR`), Pacas acumuladas del anio (`TOTALYTD`), OEE anio anterior, Variacion OEE, OEE promedio movil 3 meses (`DATESINPERIOD`) |

Las formulas siguen el catalogo: [`docs/catalogo_indicadores.md`](../docs/catalogo_indicadores.md).

**Paginas:**

| Pagina | Que responde |
|---|---|
| Resumen ejecutivo | ¿Como va el OEE y cual maquina rinde menos? Tarjetas, linea mensual por maquina, componentes y tabla resumen |
| Paros y causas | ¿Que causas concentran las horas perdidas? **Pareto**, **drill-down** (area > codigo > subsistema > detalle), MTTR y MTBF |
| Comparativo anual | ¿Mejoramos frente al mismo mes del anio pasado? Lineas por anio, matriz maquina x anio, rendimiento por turno |

Cada pagina tiene navegador de paginas y segmentadores (anio, maquina, area de impacto). Para bajar por la jerarquia de paros: en el grafico de barras de "Drill-down", activar las flechas de arriba del visual (*Activar modo de profundizacion*) y hacer clic en una barra.

## Si algo no abre o falla

Este proyecto se escribio a mano (sin abrir Power BI), asi que la primera apertura puede mostrar algun error de formato. Copiar el mensaje exacto y corregirlo; los archivos de texto permiten arreglar solo la pieza afectada (un visual, una tabla) sin rehacer el resto.

Notas de interpretacion: el rendimiento puede superar 100 % (la velocidad de referencia es un percentil 90 historico) y la calidad es un proxy; ver los supuestos S3 y S4 del catalogo.
