# Grafana: monitoreo casi en tiempo real

Grafana corre en Docker y **se configura solo al iniciar**: fuente de datos, tablero y alerta se cargan desde archivos (*provisioning*). No hay que crear nada a mano.

## Como usarlo

```powershell
docker compose up -d --wait          # levanta PostgreSQL y Grafana
```

Abrir `http://localhost:<GRAFANA_PORT>` (3001 si el 3000 esta ocupado) con el usuario y la contrasena de `GF_SECURITY_ADMIN_*` del `.env`. El tablero esta en la carpeta **BI Vinilos > Monitoreo de lineas de envasado**. Para ver datos moviendose: [`simulacion/README.md`](../simulacion/README.md).

## Que se carga automaticamente

| Archivo | Que hace |
|---|---|
| `provisioning/datasources/postgres.yml` | Crea la fuente de datos hacia PostgreSQL. Usuario y contrasena vienen de variables de entorno (`.env`), no del archivo. |
| `provisioning/dashboards/dashboards.yml` | Le indica a Grafana que cargue los JSON de `dashboards/`. |
| `dashboards/monitoreo_lineas.json` | El tablero exportado, versionado en Git. |
| `provisioning/alerting/alertas.yml` | La regla de alerta. |

Persistencia: el volumen `grafana-data` guarda el estado de Grafana y `pgdata` los datos de la base; `docker compose down` los conserva y `docker compose down -v` los borra.

## El tablero

| Panel | Tipo | Responde |
|---|---|---|
| Estado actual por maquina | Estado (stat) | ¿Que maquinas estan produciendo, con paro corto o PARADAS? |
| Alertas | Lista de alertas | ¿Hay alguna alerta activa? |
| Pacas por lectura | Serie de tiempo | ¿Como evoluciona la produccion? |
| Minutos de paro por lectura | Serie de tiempo | ¿Quien esta parando y desde cuando? (linea de umbral en 30) |
| Disponibilidad del periodo | Medidor de barras | ¿Que fraccion del tiempo estuvo produciendo cada maquina? |
| Rendimiento frente a la meta | Medidor de barras | ¿Producen lo esperado segun su velocidad de referencia? |
| Horas de paro por causa | Medidor de barras | ¿Cuales son las causas del periodo? |
| Ultimas lecturas | Tabla | Detalle de cada lectura con la causa del paro |

**Variables del tablero** (listas desplegables arriba): `Maquina` y `Turno`, ambas de seleccion multiple. Filtran todos los paneles. El selector de tiempo y el refresco de 5 s son los de Grafana.

## La alerta: "Paro prolongado en maquina"

- **Que mide:** minutos de paro de cada lectura (una lectura = una hora de produccion).
- **Cuando salta:** si en las **2 ultimas lecturas seguidas** la maquina tuvo **mas de 30 minutos** de paro. Se evalua cada 10 s.
- **Por que ese umbral:** mas de 30 min de paro en una hora es perder mas de la mitad de la hora (disponibilidad horaria por debajo de 50 %). Los ajustes y limpiezas de 5 a 20 min son normales y no requieren a mantenimiento; exigir 2 lecturas seguidas evita avisar por un paro corto aislado.
- **Una alerta por maquina:** la columna `maquina` de la consulta se convierte en etiqueta, asi que Vinilos_2 puede estar en *Firing* mientras las demas siguen en *Normal*.
- **Notificacion:** no hay correo ni mensajeria configurados (requeririan credenciales); el aviso se ve en el panel "Alertas" y en *Alerting > Alert rules*. Propuesta de evolucion: un *contact point* hacia correo o Teams para mantenimiento.

## Seguridad

Sin registro de usuarios nuevos, sin acceso anonimo, fuente de datos de solo lectura (definida por archivo) y credenciales solo en el `.env`, que no se versiona. En produccion se agregarian un usuario de base de datos de solo lectura para Grafana, HTTPS y roles por area.
