# Grafana: monitoreo casi en tiempo real

Grafana corre en Docker y **se configura solo al iniciar**: fuente de datos, tablero y alerta se cargan desde archivos (*provisioning*). No hay que crear nada a mano.

## Cómo usarlo

```powershell
docker compose up -d --wait          # levanta PostgreSQL y Grafana
```

Abrir `http://localhost:<GRAFANA_PORT>` (3001 si el 3000 está ocupado) con el usuario y la contraseña `GF_SECURITY_ADMIN_*` del `.env`. El tablero está en la carpeta **BI Vinilos › Monitoreo de líneas de envasado**. Para ver datos moviéndose: [`simulacion/README.md`](../simulacion/README.md).

## Qué se carga automáticamente

| Archivo | Qué hace |
|---|---|
| `provisioning/datasources/postgres.yml` | Crea la fuente de datos hacia PostgreSQL con el **usuario de solo lectura**. Usuario y contraseña vienen de variables de entorno (`.env`), no del archivo. |
| `provisioning/dashboards/dashboards.yml` | Le indica a Grafana que cargue los JSON de `dashboards/`. |
| `dashboards/monitoreo_lineas.json` | El tablero exportado, versionado en Git. |
| `provisioning/alerting/alertas.yml` | La regla de alerta. |

Persistencia: el volumen `grafana-data` guarda el estado de Grafana y `pgdata` los datos de la base; `docker compose down` los conserva y `docker compose down -v` los borra.

## El tablero

| Panel | Tipo | Responde |
|---|---|---|
| Estado actual por máquina | Estado (stat) | ¿Qué máquinas están produciendo, con paro corto o PARADAS? |
| Alertas | Lista de alertas | ¿Hay alguna alerta activa? |
| Pacas por lectura | Serie de tiempo | ¿Cómo evoluciona la producción? |
| Minutos de paro por lectura | Serie de tiempo | ¿Quién está parando y desde cuándo? (línea de umbral en 30) |
| Disponibilidad del periodo | Medidor de barras | ¿Qué fracción del tiempo estuvo produciendo cada máquina? |
| Rendimiento frente a la meta | Medidor de barras | ¿Producen lo esperado según su velocidad de referencia? |
| Horas de paro por causa | Medidor de barras | ¿Cuáles son las causas del periodo? |
| Últimas lecturas | Tabla | Detalle de cada lectura con la causa del paro |

**Variables del tablero** (listas desplegables arriba): `Maquina` y `Turno`, ambas de selección múltiple. Filtran todos los paneles. El selector de tiempo y el refresco de 5 s son los de Grafana.

## La alerta: "Paro prolongado en maquina"

- **Qué mide:** minutos de paro de cada lectura (una lectura = una hora de producción).
- **Cuándo salta:** si en las **2 últimas lecturas seguidas** la máquina tuvo **más de 30 minutos** de paro. Se evalúa cada 10 s.
- **Por qué ese umbral:** más de 30 min de paro en una hora es perder más de la mitad de la hora (disponibilidad horaria por debajo de 50 %). Los ajustes y limpiezas de 5 a 20 min son normales y no requieren a mantenimiento; exigir 2 lecturas seguidas evita avisar por un paro corto aislado.
- **Una alerta por máquina:** la columna `maquina` de la consulta se convierte en etiqueta, así que Vinilos_2 puede estar en *Firing* mientras las demás siguen en *Normal*.
- **Notificación:** no hay correo ni mensajería configurados (requerirían credenciales); el aviso se ve en el panel "Alertas" y en *Alerting › Alert rules*. Propuesta de evolución: un *contact point* hacia correo o Teams para mantenimiento.

## Seguridad

Sin registro de usuarios nuevos, sin acceso anónimo, fuente de datos de solo lectura (definida por archivo) y credenciales solo en el `.env`, que no se versiona. Grafana lee la base con un **usuario de solo lectura** que no ve los datos personales. En producción se agregarían HTTPS y roles por área; ver [docs/seguridad_datos_personales.md](../docs/seguridad_datos_personales.md).
