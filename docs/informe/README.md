# Informe final

## Entregable oficial

| Archivo | Qué es |
|---|---|
| **`BI_ProyectoFinal_Asprilla_Grisales.pdf`** | Informe final en PDF (portada, todos los componentes pedidos, capturas de los tableros) |
| `BI_ProyectoFinal_Asprilla_Grisales.docx` | La misma versión en Word, para poder editarla |

## Otros archivos de esta carpeta

| Archivo o carpeta | Para qué sirve |
|---|---|
| `construir_docx.py` | Genera el informe oficial (Word y PDF) a partir de los documentos del repositorio |
| `construir_pdf.py` | Genera una versión larga y opcional (`informe_completo.pdf`, que Git ignora) |
| `capturar_grafana.py` | Toma las capturas del tablero de Grafana (estado normal y con alerta) |
| `figuras/` | Diagramas del informe como imágenes (arquitectura y esquema en estrella) |
| `requirements.txt` | Librerías de Python que necesitan estos scripts |

Las capturas de Power BI y Grafana están en [`../capturas/`](../capturas/).

## Cómo regenerar el informe

El informe se arma desde los documentos de `docs/`, `etl/`, `grafana/`, `powerbi/` y `simulacion/`. Si algo cambia, se regenera con un comando. Requisitos: la base levantada con los datos cargados (lee de ella los resultados de las consultas) y **Microsoft Word** instalado (lo usa para actualizar el índice y exportar el PDF).

```
.venv\Scripts\python -m pip install -r docs\informe\requirements.txt
.venv\Scripts\python docs\informe\construir_docx.py
```

La tabla de "Historial de commits" del informe se calcula en ese momento a partir de Git; conviene regenerarlo cuando ambos integrantes hayan hecho commits.

Para volver a tomar las capturas de Grafana (con la simulación corriendo y Google Chrome instalado):

```
.venv\Scripts\python docs\informe\capturar_grafana.py
```
