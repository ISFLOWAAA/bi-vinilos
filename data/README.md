# Datos de origen

## `raw/`

Contiene la **fuente original, sin modificar**:

| Archivo | Qué es |
|---|---|
| `SEGUIMIENTO_TEMPERAS_Y_VINILOS_Actividad.xlsm` | Libro de Excel con macros donde mantenimiento transcribe los registros "hora a hora" de las operarias. Tiene 21 hojas; la principal es `Base De Datos` (8.208 registros, de enero de 2022 a marzo de 2025). |

Las hojas que usa el ETL:

| Hoja | Uso |
|---|---|
| `Base De Datos` | Producción y paros: es la fuente de todos los hechos |
| `TABLA CODIGOS` | Jerarquía de códigos de paro y subcódigos (hoja oculta) |

Las demás hojas son tablas dinámicas, gráficos y el formulario de captura del informe actual; el diagnóstico las describe en [docs/diagnostico/diagnostico_fuente.md](../docs/diagnostico/diagnostico_fuente.md).

## Reglas

- **No se edita.** El ETL solo lo lee; si algo se corrige, se corrige en el ETL y queda registrado, no en el Excel.
- **Contiene datos personales** (nombres de operarias y del personal de mantenimiento). Por eso el repositorio es privado y el modelo analítico solo guarda códigos seudónimos; ver [docs/seguridad_datos_personales.md](../docs/seguridad_datos_personales.md).
- El procedimiento original P-MTO-22 que explica los códigos de paro está en [docs/](../docs/).

## Cómo se usa

No hay que hacer nada: `iniciar.ps1`, `iniciar.sh` o `python etl/main.py` lo leen directamente desde aquí. El ETL no escribe en esta carpeta.
