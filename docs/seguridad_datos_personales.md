# Datos personales y seguridad de acceso

## 1. Qué datos personales hay

| Dato | Dónde aparece en la fuente | Sensibilidad |
|---|---|---|
| Nombre de las operarias y operarios | Columna `Operario` (32 personas distintas tras la limpieza) | Dato personal; permite asociar productividad y paros a una persona |
| Nombre del personal de mantenimiento | Columna `Personal involucrado` (38 nombres) | Dato personal |
| Observaciones de paro | Texto libre, puede nombrar a alguien | Posible dato personal |

El marco aplicable en Colombia es la **Ley 1581 de 2012** de protección de datos personales: finalidad clara, uso limitado a esa finalidad, acceso restringido y conservación solo mientras sea necesaria.

## 2. Cómo se trató

| Principio | Qué se hizo |
|---|---|
| **Minimización** | Los análisis de la dirección no necesitan saber *quién* operó, sino la máquina, el turno y la causa. Por eso el modelo analítico no contiene nombres. |
| **Seudonimización** | Cada operario recibe un código `OP-nnn` (`dw.dim_operario`). El nombre real vive solo en `seguridad.operario_pii`, en un esquema aparte. |
| **No se carga lo que no se necesita** | `Personal involucrado` (nombres del personal de mantenimiento) no se carga al modelo. Tampoco se cargan las observaciones de texto libre. |
| **Los tableros no ven nombres** | Power BI no importa `seguridad` ni `calidad`; Grafana lee con un usuario que no tiene permiso sobre esos esquemas. |
| **Fuera del repositorio** | El Excel original está en `data/raw/` y el repositorio es privado. No se versiona ningún `.env`. |

## 3. Seguridad de acceso

### Base de datos: mínimo privilegio

| Usuario | Para qué | Permisos |
|---|---|---|
| `bi_user` (administrador) | ETL, simulación y mantenimiento | Todos (propietario de la base) |
| `bi_lector` | Grafana, y recomendado para Power BI | Solo `SELECT` sobre el esquema `dw`. **No puede** leer `seguridad` ni `calidad`, ni insertar, modificar o borrar |

Está definido en `sql/init/04_roles.sh` y se comprobó que `bi_lector` recibe `permission denied` al intentar leer `seguridad.operario_pii` o borrar de `dw`.

### Grafana

- Sin registro de usuarios nuevos y **sin acceso anónimo**.
- Fuente de datos definida por archivo y de solo lectura (no se puede editar desde la interfaz).
- Credenciales y contraseñas en variables de entorno (`.env`), nunca en los archivos versionados.
- La contraseña del administrador se define en el `.env` y se cambia desde allí.

### Power BI

- Las credenciales de la base **no se guardan en el proyecto**: Power BI las pide y las conserva solo en el equipo de quien lo abre.
- Conectar con `bi_lector` en lugar de `bi_user`.
- El archivo `.pbix` publicado y compartido mostraría los datos del modelo, por lo que no incluye nombres de personas.

### Repositorio

- Repositorio **privado** en GitHub; el `.gitignore` excluye `.env`, cachés de Power BI y volúmenes.
- Se versiona `.env.example` con valores de ejemplo (`cambia_esta_clave`).

## 4. Qué falta para producción

Lo implementado es adecuado para el proyecto y la demostración. En una planta real se agregaría:

| Medida | Por qué |
|---|---|
| HTTPS en Grafana y conexión cifrada a la base (SSL) | Hoy el tráfico es local y sin cifrar |
| Autenticación corporativa (Microsoft Entra ID, LDAP) y roles por área | Que supervisores vean solo su línea y la dirección vea todo |
| Seguridad a nivel de fila (RLS) en Power BI | Limitar qué máquinas ve cada persona |
| Contraseñas en un gestor de secretos y rotación periódica | Hoy las contraseñas de desarrollo son simples |
| Copias de seguridad cifradas y política de retención | Conservar solo el tiempo necesario |
| Aviso y autorización de tratamiento de datos a los trabajadores | Obligación de transparencia de la Ley 1581 |
| Revisión del tratamiento con el área jurídica | Este documento es técnico y no reemplaza una asesoría legal |
