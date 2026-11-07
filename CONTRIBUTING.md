# Cómo colaborar

Guía corta para trabajar en equipo en este repositorio.

## Primeros pasos

1. Pedir acceso al repositorio y clonarlo: `git clone https://github.com/ISFLOWAAA/bi-vinilos.git`
2. Configurar la identidad de Git (para que los commits queden a nombre de cada persona):
   `git config user.name "Nombre Apellido"` y `git config user.email "correo@ejemplo.com"`
3. Levantar el proyecto con `iniciar.ps1` (Windows) o `iniciar.sh` (Linux, macOS, Git Bash). Detalle en el [README](README.md).

## Flujo de trabajo

Para mantener el historial limpio y ordenado, se recomienda el uso de ramas temáticas (*feature branches*) y la convención de commits estandarizada:

```bash
git pull                            # traer lo último de main
git checkout -b feature/nombre-funcionalidad  # crear rama de feature (o fix/..., docs/...)
# ... realizar cambios y verificar ...
git add <archivos>                  # nunca "git add ." sin revisar con "git status"
git commit -m "FEATURE: descripción clara del cambio"
git push -u origin feature/nombre-funcionalidad  # abrir Pull Request para revisión en equipo
```

### Convención de Commits

Utilizar prefijos en mayúsculas para clasificar claramente cada contribución:

- `FEATURE: <mensaje>`: Nuevas funcionalidades, indicadores, capacidades del ETL o tableros.
- `FIX: <mensaje>`: Corrección de errores en scripts, consultas SQL o visualizaciones.
- `DOCS: <mensaje>`: Actualizaciones en la documentación, glosario o informe final.
- `TEST: <mensaje>`: Incorporación o ajuste de pruebas unitarias.
- `REFACTOR: <mensaje>`: Mejoras de estructura de código o limpieza sin alterar el comportamiento.

Los commits pequeños y con un mensaje claro hacen visible el aporte de cada integrante.

## Antes de hacer commit

- **Nunca subir contraseñas.** El `.env` está ignorado; revisar con `git status` que no aparezca.
- Si se cambia el ETL: `python -m pytest etl/tests` y volver a correr `etl/main.py` (debe terminar en `TODO CUADRA`).
- Si se cambia el DDL (`sql/init/`): recrear la base con `docker compose down -v` y `iniciar.ps1`, porque esos archivos solo se ejecutan con la base vacía.
- Si se cambia un documento: regenerar el informe oficial con `python docs/informe/construir_docx.py` (necesita Microsoft Word; ver [docs/informe/](docs/informe/)).
- Si se edita el Power BI en el programa, **cerrar y guardar antes de hacer commit**; Power BI reescribe los archivos del proyecto al guardar.

## Dónde está cada cosa

| Quiero cambiar… | Archivo |
|---|---|
| Una regla de limpieza | `etl/limpiar.py` (con pruebas en `etl/tests/`) |
| Cómo se arma el modelo | `etl/transformar.py` |
| Una tabla, restricción o índice | `sql/init/01_ddl.sql` |
| Una consulta analítica | `sql/consultas/consultas_analiticas.sql` |
| Un panel o la alerta de Grafana | `grafana/dashboards/monitoreo_lineas.json`, `grafana/provisioning/alerting/alertas.yml` |
| Una medida DAX | `powerbi/BI_Vinilos.SemanticModel/definition/tables/fact_produccion.tmdl` |
| La simulación | `simulacion/simular.py` |
| Un parámetro (umbrales, puertos) | [docs/configuracion.md](docs/configuracion.md) |
