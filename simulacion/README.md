# Simulación de datos hora a hora

Un tablero de monitoreo solo demuestra algo si los datos se mueven. Este script emula las lecturas que llegarían de las líneas y las inserta en `dw.fact_registro_horario`; Grafana las lee y refresca el tablero cada 5 segundos.

## Cómo correrlo (con la base levantada y el ETL ejecutado)

```powershell
.venv\Scripts\python simulacion\simular.py                         # lecturas cada 10 s, sin límite
.venv\Scripts\python simulacion\simular.py --provocar Vinilos_2    # en OTRA terminal: fuerza una falla larga
.venv\Scripts\python simulacion\simular.py --normalizar            # quita la falla
.venv\Scripts\python simulacion\simular.py --reiniciar             # borra lo simulado y empieza de cero
```

Opciones: `--intervalo` (segundos entre lecturas), `--historial` (lecturas pasadas que crea al empezar, para que el gráfico no arranque vacío), `--ciclos` (parar tras N lecturas), `--semilla` (resultados repetibles).

## Qué simula

Cada **lectura** equivale a **una hora de producción** de una máquina. En la demo se emite una cada 10 s en lugar de cada 3.600 s; con `--intervalo 3600` sería en tiempo real.

| Dato | De dónde sale |
|---|---|
| Pacas de la hora | Velocidad de referencia de la máquina y referencia (`dim_meta_velocidad`), por la fracción de hora trabajada, con variación aleatoria alrededor del 90 % |
| Referencia | Una de las que esa máquina corrió en el histórico; cambia de vez en cuando |
| Paro | 20 % de las lecturas, de 3 a 40 minutos; la causa se sortea según la frecuencia histórica de causas **no programadas** (`fact_paro`) |
| Turno y hora | Calculados con la hora de Colombia (UTC−5): turno 1 de 6 a 14, turno 2 de 14 a 22, turno 3 de 22 a 6 |
| Falla provocada | La máquina elegida reporta de 42 a 58 minutos de paro con causa "Falla del sistema electromecánico" hasta que se normalice |

`fecha_hora` se guarda en **UTC**, que es lo que Grafana espera de una columna `timestamp`; la fecha y la hora del modelo (`fecha_key`, `hora_key`) van en hora local.

El simulador sigue corriendo hasta que se detiene con Ctrl + C. Si quedó en segundo plano, el ETL (`etl/main.py`) también borra las lecturas simuladas al recargar.

## Guion para la sustentación

1. `docker compose up -d --wait` y abrir Grafana (`http://localhost:<GRAFANA_PORT>`).
2. Arrancar `simular.py`: el tablero se mueve solo.
3. En otra terminal: `simular.py --provocar Vinilos_2`. La máquina pasa a **PARADA** en el panel de estado y, tras 2 lecturas seguidas con más de 30 min de paro, la alerta **"Paro prolongado en maquina"** pasa a *Firing* (se ve en el panel "Alertas").
4. `simular.py --normalizar`: la máquina se recupera y la alerta vuelve a *Normal*.
