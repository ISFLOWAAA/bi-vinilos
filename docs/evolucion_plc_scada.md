# Evolución: datos directos desde PLC y SCADA

Hoy los datos nacen en papel, pasan por un Excel y llegan a la base con días de retraso. Si las líneas entregaran sus señales directamente desde los **PLC** o el **SCADA**, el modelo y los tableros se mantendrían; cambiaría solo cómo entran los datos.

## Arquitectura propuesta

```
PLC de cada línea ──► Gateway OPC UA / Modbus ──► Broker MQTT ──► Procesador de flujo ──► PostgreSQL / TimescaleDB ──► Power BI · Grafana
 (contadores, estados,    (convierte el protocolo      (cola de       (agrega por hora,        (mismo modelo estrella +       (sin cambios en
  códigos de paro)         de la máquina)               mensajes)      valida, enriquece)       tabla de eventos)               las definiciones)
```

| Componente | Función | Ejemplos |
|---|---|---|
| PLC y sensores | Cuentan envases, miden tiempo en marcha y registran el estado de la máquina | Contador de envases, sensor de paro, selector de código de paro en el HMI |
| Gateway | Traduce el protocolo del equipo a un estándar abierto | OPC UA, Modbus TCP |
| Broker de mensajes | Desacopla las máquinas de la base, absorbe picos y evita pérdida de datos si algo se cae | MQTT (Mosquitto, EMQX) |
| Procesador de flujo | Convierte señales crudas en lecturas por hora y eventos de paro, descarta ruido | Python, Node-RED o Telegraf |
| Base de series de tiempo | Guarda lecturas de alta frecuencia con compresión y retención | TimescaleDB (extensión de PostgreSQL) |

## Qué cambia y qué no

| Aspecto | Hoy | Con PLC o SCADA |
|---|---|---|
| Latencia | Días (transcripción manual) | Segundos |
| Producción | Pacas por jornada, digitadas | Conteo automático por hora o por minuto |
| Paros | Código y duración digitados | Inicio y fin medidos por la máquina; el operario confirma solo la causa |
| Calidad | No se registra | Rechazos contados por inspección en línea |
| Meta | Se digita y no se guarda | Velocidad nominal configurada en el PLC y guardada como dato |
| `fact_registro_horario` | Lo llena una simulación | Lo llena el procesador de flujo, con la misma estructura |
| `fact_produccion` y `fact_paro` | Los llena el ETL desde el Excel | Se alimentan al cierre de cada turno desde los datos del PLC |
| Dimensiones, medidas DAX, tablero y alerta | — | **Se conservan** |

## Beneficios para los problemas encontrados en el diagnóstico

- **Fin de los problemas de calidad de captura:** desaparecen los duplicados, los subcódigos en dos catálogos, los turnos nulos (47 % de las jornadas) y las pacas digitadas como unidades.
- **OEE real:** con velocidad ideal y rechazos medidos, rendimiento y calidad dejan de ser una aproximación.
- **Alertas útiles:** el umbral de 30 minutos se podría reducir a minutos, y agregar alertas por producción por debajo de la meta.
- **Mantenimiento predictivo:** con señales de vibración o corriente de motores y sensores se pueden anticipar las fallas electromecánicas en lugar de reaccionar a ellas.

## Riesgos y cómo mitigarlos

| Riesgo | Mitigación |
|---|---|
| Seguridad de la red industrial (IT y OT) | Segmentar la red, usar OPC UA con certificados y publicar solo hacia afuera, nunca hacia los PLC |
| Calidad de la señal (falsos paros) | Reglas de filtrado en el procesador de flujo y confirmación del operario |
| Equipos antiguos sin comunicación | Sensores y contadores añadidos de forma externa, sin tocar el control de la máquina |
| Volumen de datos | Agregar a hora o minuto para el modelo analítico y conservar lo crudo solo un tiempo limitado |

## Ruta de implementación sugerida

1. **Piloto en una línea** (por ejemplo Vinilos_2, la de menor OEE): conteo y estado, comparado en paralelo contra el formato en papel.
2. **Validar** diferencias durante un mes y ajustar las reglas de cálculo.
3. **Extender** a las otras tres líneas y retirar la transcripción manual.
4. **Agregar** calidad en línea y mantenimiento predictivo.
