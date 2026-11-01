# Simulacion de datos hora a hora

Un tablero de monitoreo solo demuestra algo si los datos se mueven. Este script emula las lecturas que llegarian de las lineas y las inserta en `dw.fact_registro_horario`; Grafana las lee y refresca el tablero cada 5 segundos.

## Como correrlo (con la base levantada y el ETL ejecutado)

```powershell
.venv\Scripts\python simulacion\simular.py                         # lecturas cada 10 s, sin limite
.venv\Scripts\python simulacion\simular.py --provocar Vinilos_2    # en OTRA terminal: fuerza una falla larga
.venv\Scripts\python simulacion\simular.py --normalizar            # quita la falla
.venv\Scripts\python simulacion\simular.py --reiniciar             # borra lo simulado y empieza de cero
```

Opciones: `--intervalo` (segundos entre lecturas), `--historial` (lecturas pasadas que crea al empezar, para que el grafico no arranque vacio), `--ciclos` (parar tras N lecturas), `--semilla` (resultados repetibles).

## Que simula

Cada **lectura** equivale a **una hora de produccion** de una maquina. En la demo se emite una cada 10 s en lugar de cada 3.600 s; con `--intervalo 3600` seria en tiempo real.

| Dato | De donde sale |
|---|---|
| Pacas de la hora | Velocidad de referencia de la maquina y referencia (`dim_meta_velocidad`), por la fraccion de hora trabajada, con variacion aleatoria alrededor del 90 % |
| Referencia | Una de las que esa maquina corrio en el historico; cambia de vez en cuando |
| Paro | 20 % de las lecturas, de 3 a 40 minutos; la causa se sortea segun la frecuencia historica de causas **no programadas** (`fact_paro`) |
| Turno y hora | Calculados con la hora de Colombia (UTC-5): turno 1 de 6 a 14, turno 2 de 14 a 22, turno 3 de 22 a 6 |
| Falla provocada | La maquina elegida reporta de 42 a 58 minutos de paro con causa "Falla del sistema electromecanico" hasta que se normalice |

`fecha_hora` se guarda en **UTC**, que es lo que Grafana espera de una columna `timestamp`; la fecha y la hora del modelo (`fecha_key`, `hora_key`) van en hora local.

## Guion para la sustentacion

1. `docker compose up -d --wait` y abrir Grafana (`http://localhost:<GRAFANA_PORT>`).
2. Arrancar `simular.py`: el tablero se mueve solo.
3. En otra terminal: `simular.py --provocar Vinilos_2`. La maquina pasa a **PARADA** en el panel de estado y, tras 2 lecturas seguidas con mas de 30 min de paro, la alerta **"Paro prolongado en maquina"** pasa a *Firing* (se ve en el panel "Alertas").
4. `simular.py --normalizar`: la maquina se recupera y la alerta vuelve a *Normal*.
