# Validacion del ETL

Informe generado automaticamente por `python etl/main.py` (`etl/validar.py`). No editar a mano.

## 1. Reglas de limpieza aplicadas (antes y despues)

| Regla | Antes | Despues | Detalle |
|---|---:|---:|---|
| Eliminar duplicados exactos | 8,208 | 8,166 | 42 filas copia de otra fila |
| Separar jornadas y filas de subcodigo | 8,166 | 5,138 | 3028 filas de subcodigo no son jornadas: solo aportan a paros |
| Unificar turnos | 8 | 7 | valores crudos (incluye nulo) -> turnos distintos; 2605 jornadas quedan 'Sin turno'; 0 valores no reconocidos |
| Estandarizar referencias | 52 | 48 | nombres crudos -> referencias unicas (erratas y formato corregidos); 4181 filas sin referencia (Desconocida) |
| Seudonimizar operarios | 34 | 32 | nombres crudos -> operarios con codigo OP-nnn ('No' y 'No aplica' son nulos); 4236 filas sin operario (Desconocido) |
| Anular pacas atipicas | 5,135 | 5,124 | 11 jornadas con mas de 60 pacas/h (52,493 pacas); se conserva el valor en pacas_origen |
| Marcar jornadas con datos dudosos | 5,138 | 439 | se cargan con bandera_calidad: pacas_atipicas=11, sin_pacas=3, sin_horas=1, cero_pacas=421, cero_horas=396, paro_mayor_horas=45 |
| Jornadas validas para calcular rendimiento | 5,138 | 4,715 | con pacas validas y horas productivas > 0 |
| Calcular velocidad de referencia (SCD tipo 2) | 5,138 | 68 | 68 versiones de meta; 4879 jornadas usan la meta de su referencia, 259 usan la general de la maquina |
| Despivotar 18 pares codigo/horas | 146,988 | 16,482 | celdas de codigo -> eventos de paro con horas > 0 |
| Normalizar subcodigos | 67 | 59 | textos crudos -> hojas de jerarquia usadas; eventos: 2644 ok, 940 del catalogo antiguo (4.x -> 5.x), 12898 sin subcodigo, 0 no reconocidos, 0 sin hoja en el catalogo |
| Hoja oculta 'Base de datos de Sub codigos' | 1,252 | 0 | no se carga: sus 1.252 filas ya estan todas en 'Base De Datos' (verificado por fecha, maquina, operario y referencia) |

## 2. Cuadre de totales contra la fuente

Regla: **fuente − ajuste = cargado**. El ajuste son las filas duplicadas eliminadas y las pacas atipicas anuladas (ver seccion 1).

| Medida | Fuente (Excel) | Ajuste | Cargado en la base | Diferencia | Estado |
|---|---:|---:|---:|---:|---|
| Pacas producidas | 378,778.00 | 53,512.00 | 325,266.00 | 0.0000 | OK |
| Horas trabajadas (programadas) | 38,063.35 | 129.00 | 37,934.35 | 0.0000 | OK |
| Tiempo de paro (horas) | 8,449.65 | 18.12 | 8,431.54 | -0.0004 | OK |
| Horas del codigo 01 | 323.90 | 1.32 | 322.58 | -0.0000 | OK |
| Horas del codigo 02 | 32.58 | 0.00 | 32.58 | -0.0000 | OK |
| Horas del codigo 03 | 87.13 | 0.58 | 86.55 | -0.0000 | OK |
| Horas del codigo 04 | 8.50 | 0.00 | 8.50 | 0.0000 | OK |
| Horas del codigo 05 | 1,819.33 | 5.63 | 1,813.69 | -0.0000 | OK |
| Horas del codigo 06 | 1,546.90 | 1.08 | 1,545.82 | 0.0000 | OK |
| Horas del codigo 07 | 620.81 | 0.00 | 620.81 | -0.0000 | OK |
| Horas del codigo 08 | 68.13 | 0.00 | 68.13 | -0.0000 | OK |
| Horas del codigo 09 | 182.13 | 0.33 | 181.80 | -0.0000 | OK |
| Horas del codigo 10 | 356.38 | 0.00 | 356.38 | 0.0000 | OK |
| Horas del codigo 11 | 9.05 | 0.00 | 9.05 | 0.0000 | OK |
| Horas del codigo 12 | 227.02 | 0.35 | 226.67 | 0.0000 | OK |
| Horas del codigo 13 | 19.13 | 0.00 | 19.13 | 0.0000 | OK |
| Horas del codigo 14 | 253.47 | 0.00 | 253.47 | -0.0000 | OK |
| Horas del codigo 15 | 165.83 | 1.20 | 164.63 | -0.0000 | OK |
| Horas del codigo 16 | 2,002.55 | 2.33 | 2,000.22 | -0.0004 | OK |
| Horas del codigo 17 | 718.43 | 5.28 | 713.15 | -0.0000 | OK |
| Horas del codigo 18 | 8.37 | 0.00 | 8.37 | 0.0000 | OK |

## 3. Cuadre por maquina y anio

- Produccion: 16 combinaciones de maquina y anio comparadas (jornadas, pacas y horas). Diferencia maxima: **0.0000** → OK.
- Paros: 16 combinaciones comparadas (eventos y horas). Diferencia maxima: **0.0001** → OK.
- Filas cargadas: 5,138 jornadas y 16,482 eventos de paro → OK.
- Incidencias de calidad registradas en `calidad.incidencias`: 53.

## 4. Conclusion

**El proceso cuadra con la fuente.** Toda diferencia entre el Excel y la base esta explicada por los duplicados eliminados y las pacas atipicas anuladas, y queda registrada fila por fila en `calidad.incidencias`.
