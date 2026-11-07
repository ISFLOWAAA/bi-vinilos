## Descripción de la Feature / Cambio

<!-- Describe de forma concisa qué aporta este Pull Request y cuál es su objetivo. -->

## Tipo de Cambio

- [ ] `FEATURE`: Nueva funcionalidad, indicador o capacidad analítica
- [ ] `FIX`: Corrección de un fallo o error detectado
- [ ] `DOCS`: Actualización o adición a la documentación o informe
- [ ] `TEST`: Pruebas unitarias o de validación
- [ ] `REFACTOR`: Refactorización o mejora estructural sin cambio funcional

## Módulos Afectados

- [ ] ETL (`etl/`)
- [ ] Base de datos / DDL (`sql/`)
- [ ] Monitoreo Grafana (`grafana/`)
- [ ] Tablero Power BI (`powerbi/`)
- [ ] Simulación (`simulacion/`)
- [ ] Documentación / Informes (`docs/`)

## Lista de Verificación (Checklist)

- [ ] El título del commit/PR sigue la convención (`FEATURE: ...`, `FIX: ...`, etc.).
- [ ] No se suben contraseñas ni archivos `.env`.
- [ ] Las pruebas unitarias pasan exitosamente (`python -m pytest`).
- [ ] Si se modificó el ETL, `python etl/main.py` finaliza en `TODO CUADRA`.
- [ ] Si se modificó el DDL, se verificó el despliegue con la base de datos limpia.
- [ ] La documentación relevante fue actualizada.
