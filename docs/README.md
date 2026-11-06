# Documentación del proyecto

Aquí está todo lo que explica el proyecto, desde el problema hasta cómo operarlo. No hace falta leerlo en orden: elige según lo que quieras saber. Si algún término no te suena (OEE, MTTR, esquema en estrella…), consulta el [glosario](glosario.md).

## ¿Qué quieres saber?

| Quiero… | Lee |
|---|---|
| Entender de qué trata el proyecto y qué se encontró | [Resumen ejecutivo](resumen_ejecutivo.md) |
| Saber de dónde vienen los datos y qué problemas tenían | [Diagnóstico de la fuente](diagnostico/diagnostico_fuente.md) |
| Saber qué se mide, para quién y con qué fórmula | [Catálogo de indicadores](catalogo_indicadores.md) |
| Entender cómo se diseñó la base de datos | [Modelo dimensional](modelo_dimensional.md) y luego el [diccionario de datos](diccionario_datos.md) |
| Ver las restricciones, índices y consultas | [Base de datos](base_de_datos.md) |
| Comprobar que los datos cargados cuadran con el Excel | [Validación del ETL](validacion_etl.md) |
| Ver cómo encaja todo, de la fuente al tablero | [Arquitectura](arquitectura.md) |
| Saber por qué hay dos herramientas (Power BI y Grafana) | [Comparativo Power BI y Grafana](comparativo_power_bi_grafana.md) |
| Imaginar cómo crecería con datos directos de las máquinas | [Evolución con PLC o SCADA](evolucion_plc_scada.md) |
| Saber cómo se protegen los datos personales y el acceso | [Seguridad y datos personales](seguridad_datos_personales.md) |
| Instalar, configurar o arreglar un problema | [Configuración y solución de problemas](configuracion.md) |
| Ver el informe final entregado | [`informe/`](informe/) |

## Documentos por etapa del proyecto

| Etapa | Documento | Pregunta que responde |
|---|---|---|
| 1. Entender | [diagnostico/diagnostico_fuente.md](diagnostico/diagnostico_fuente.md) | ¿Qué datos hay y qué tan buenos son? |
| 2. Definir | [catalogo_indicadores.md](catalogo_indicadores.md) | ¿Qué hay que medir y para quién? |
| 3. Diseñar | [modelo_dimensional.md](modelo_dimensional.md) | ¿Cómo se organizan los datos para analizarlos? |
| 3. Diseñar | [diccionario_datos.md](diccionario_datos.md) | ¿Qué significa cada columna y de dónde sale? |
| 4. Construir | [base_de_datos.md](base_de_datos.md) | ¿Cómo se protege y se acelera la base? |
| 4. Construir | [validacion_etl.md](validacion_etl.md) | ¿Qué se limpió y por qué los totales cuadran? |
| 5. Consumir | [arquitectura.md](arquitectura.md), [comparativo_power_bi_grafana.md](comparativo_power_bi_grafana.md) | ¿Cómo se usan los datos y con qué herramienta? |
| 6. Proteger y evolucionar | [seguridad_datos_personales.md](seguridad_datos_personales.md), [evolucion_plc_scada.md](evolucion_plc_scada.md) | ¿Es seguro? ¿Hacia dónde puede crecer? |
| Comunicar | [resumen_ejecutivo.md](resumen_ejecutivo.md) | ¿Qué le decimos a la gerencia? |

## Documentos que se generan solos

Estos dos **no se editan a mano**, porque cada ejecución los reescribe:

| Archivo | Lo genera | Cuándo |
|---|---|---|
| [validacion_etl.md](validacion_etl.md) | `python etl/main.py` | Cada vez que corre el ETL |
| [diccionario_datos.md](diccionario_datos.md) | `python etl/diccionario.py` | Cuando cambia la estructura de la base |

## Otras carpetas de `docs/`

| Carpeta o archivo | Contenido |
|---|---|
| [`informe/`](informe/) | **Informe final oficial** (PDF y Word) y los scripts que lo generan |
| `capturas/` | Capturas de pantalla de Power BI y Grafana usadas en el informe |
| `diagnostico/` | Diagnóstico de la fuente de datos |
| `P-MTO-22_Registro_paros_de_produccion.pdf` | Procedimiento original de la empresa para registrar paros |
| `arquitectura.svg`, `modelo_estrella.svg` | Diagramas (se ven directamente en GitHub) |

Documentación de cada herramienta, junto a su código: [etl](../etl/README.md) · [sql](../sql/README.md) · [simulación](../simulacion/README.md) · [Grafana](../grafana/README.md) · [Power BI](../powerbi/README.md) · [datos](../data/README.md).
