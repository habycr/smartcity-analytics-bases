# SmartCity Analytics

Sistema de análisis de datos urbanos utilizando PostgreSQL,
MongoDB, Hadoop y Apache Spark.

## 1. PostgreSQL: Modelo e ingestión de datos

### 1.1 Modelo conceptual Chen

![Modelo conceptual Chen](../docs/postgres/modelo_chen.png)

[Ver diagrama en PDF](../docs/postgres/modelo_chen.pdf)

### 1.2 Modelo lógico relacional

![Modelo lógico relacional](../docs/postgres/modelo_relacional.png)

[Ver diagrama en PDF](../docs/postgres/modelo_relacional.pdf)

### 1.3 Normalización

### 1.3.1. Decisiones de diseño

Se parte de las cinco entidades mínimas exigidas en el enunciado (`SENSOR`, `UBICACION`, `CATEGORIA_SENSOR`, `USUARIO`, `ORGANISMO_RESPONSABLE`) y de la entidad `MEDICION` propuesta para el primer sprint. Se agregan dos entidades de catálogo para expresar las reglas de negocio acordadas:

- **TIPO_SENSOR:** cada tipo de sensor pertenece a una **única categoría**. El atributo `tipo_sensor` se conserva en `SENSOR`, ahora como referencia al catálogo de tipos.
- **VARIABLE_MEDICION:** cada variable tiene **una unidad canónica** compatible con el Sistema Internacional o aceptada para su uso con él. Para EPA AQS, las mediciones se almacenan en µg/m³; PM2.5 y PM10 conservan condiciones de referencia diferentes en el origen, sin conversión termodinámica.

`USUARIO` se mantiene **independiente** de los organismos; puede representar a personas comunes. Su atributo compuesto `nombre` se desglosa en `nombre`, `apellido1` y `apellido2`; `coordenadas` en `latitud` y `longitud`.

> **Alcance:** estas dos entidades adicionales y las cardinalidades son decisiones del equipo para lograr consistencia; no aparecen como entidades mínimas obligatorias en el enunciado. Las unidades de origen se verificaron con los archivos EPA AQS; las condiciones de referencia originales no se guardan por medición en el esquema actual.

### 1.3.2. Transformación de Chen al modelo relacional

Cada entidad se convierte en una tabla. En cada relación **1:N** se añade al lado **N** una FK hacia la PK del lado **1**, sin tabla intermedia. Las participaciones totales acordadas se traducen a FK `NOT NULL`.

```text
UBICACION(
  id_ubicacion [PK], 
  nombre_zona, 
  distrito, 
  latitud, 
  longitud
)

CATEGORIA_SENSOR(
  id_categoria [PK], 
  nombre_categoria
)

TIPO_SENSOR(
  tipo_sensor [PK],
  id_categoria [FK -> CATEGORIA_SENSOR(id_categoria)]
)

ORGANISMO_RESPONSABLE(
  id_organismo [PK], 
  nombre, 
  responsable
)

USUARIO(
  id_usuario [PK], 
  nombre, 
  apellido1, 
  apellido2, 
  correo
)

SENSOR(
  id_sensor [PK], 
  nombre,
  tipo_sensor [FK -> TIPO_SENSOR(tipo_sensor)],
  fecha_instalacion, 
  estado,
  id_ubicacion [FK -> UBICACION(id_ubicacion)],
  id_organismo [FK -> ORGANISMO_RESPONSABLE(id_organismo)]
)

VARIABLE_MEDICION(
  id_variable [PK], 
  nombre_variable, 
  unidad_canonica
)

MEDICION(
  id_medicion [PK],
  id_sensor [FK -> SENSOR(id_sensor)],
  id_variable [FK -> VARIABLE_MEDICION(id_variable)],
  fecha_utc, 
  valor, 
  fuente
)
```

#### Relaciones transformadas

| Relación Chen | Cardinalidad | FK en el modelo relacional | Participación total |
|---|---|---|---|
| UBICACION — SE_INSTALA_EN — SENSOR | 1:N | `SENSOR.id_ubicacion` | SENSOR |
| CATEGORIA_SENSOR — CLASIFICA — TIPO_SENSOR | 1:N | `TIPO_SENSOR.id_categoria` | TIPO_SENSOR |
| TIPO_SENSOR — ES_DE_TIPO — SENSOR | 1:N | `SENSOR.tipo_sensor` | SENSOR |
| ORGANISMO_RESPONSABLE — ADMINISTRA — SENSOR | 1:N | `SENSOR.id_organismo` | SENSOR |
| SENSOR — GENERA — MEDICION | 1:N | `MEDICION.id_sensor` | MEDICION |
| VARIABLE_MEDICION — CORRESPONDE_A — MEDICION | 1:N | `MEDICION.id_variable` | MEDICION |

**Resultado:** 8 tablas, 8 claves primarias y 6 claves foráneas. Se permiten sensores sin mediciones y usuarios sin organismo asociado.

### 1.3.3. Normalización

#### 1.3.3.1. Primera Forma Normal (1FN)

**Criterio:** valores atómicos, sin grupos repetitivos.

**Aplicación:** se descompone `coordenadas` en `latitud` y `longitud`, y el nombre compuesto de `USUARIO` en `nombre`, `apellido1` y `apellido2`. Cada registro de `MEDICION` almacena una observación con valor numérico y fecha.

**Resultado:** las ocho relaciones se plantean en **1FN**.

#### 1.3.3.2. Segunda Forma Normal (2FN)

**Criterio:** cumplir 1FN y no tener dependencias parciales respecto de una clave candidata compuesta.

**Aplicación:** las claves primarias propuestas son simples (`id_ubicacion`, `id_categoria`, `tipo_sensor`, `id_organismo`, `id_usuario`, `id_sensor`, `id_variable`, `id_medicion`). No hay dependencias parciales respecto de esas claves; se deberán revisar otras posibles claves candidatas al fijar las restricciones definitivas.

**Resultado:** se satisface **2FN** bajo las claves y dependencias de negocio declaradas.

#### 1.3.3.3. Tercera Forma Normal (3FN)

**Criterio formal:** para cada dependencia funcional no trivial `X -> A`, `X` debe ser superclave o `A` debe ser atributo primo de alguna clave candidata.

**Problema 1 — SENSOR (diseño anterior):**

```text
id_sensor -> tipo_sensor -> id_categoria
```

Si cada tipo tiene una sola categoría, `tipo_sensor -> id_categoria` crea una dependencia transitiva problemática en la tabla SENSOR anterior. **Normalización:** mover esa asociación a `TIPO_SENSOR(tipo_sensor, id_categoria)`, conservar `SENSOR.tipo_sensor` como FK y eliminar `SENSOR.id_categoria`.

**Problema 2 — MEDICION (diseño anterior):**

```text
id_medicion -> variable -> unidad
```

Si cada variable se almacena con una unidad canónica, `variable -> unidad` crea una dependencia transitiva problemática en MEDICION. **Normalización:** definir `VARIABLE_MEDICION(id_variable, nombre_variable, unidad_canonica)` y sustituir `variable`/`unidad` en MEDICION por `id_variable` como FK.

**Dependencias funcionales fundamentales del esquema nuevo:**

| Tabla | Dependencia funcional prevista |
|---|---|
| `UBICACION` | `id_ubicacion -> nombre_zona, distrito, latitud, longitud` |
| `CATEGORIA_SENSOR` | `id_categoria -> nombre_categoria` |
| `TIPO_SENSOR` | `tipo_sensor -> id_categoria` |
| `ORGANISMO_RESPONSABLE` | `id_organismo -> nombre, responsable` |
| `USUARIO` | `id_usuario -> nombre, apellido1, apellido2, correo` |
| `SENSOR` | `id_sensor -> nombre, tipo_sensor, fecha_instalacion, estado, id_ubicacion, id_organismo` |
| `VARIABLE_MEDICION` | `id_variable -> nombre_variable, unidad_canonica` y, si nombre es único, `nombre_variable -> id_variable, unidad_canonica` |
| `MEDICION` | `id_medicion -> id_sensor, id_variable, fecha_utc, valor, fuente` |

**Resultado:** se eliminaron las **dos dependencias transitivas identificadas**. Con las dependencias de negocio declaradas y sin otras dependencias adicionales, el esquema propuesto **satisface 3FN**. Esta conclusión requiere confirmar las claves candidatas, la unicidad de nombres de catálogo y el significado exacto de `responsable`, `nombre_zona` y `fuente` al validar los datos reales; no equivale aún a una prueba exhaustiva frente a cualquier conjunto de datos.



## 2. Implementación PostgreSQL y despliegue

### 2.1. Entorno y archivos

El esquema se implementó en **PostgreSQL 16**, se verificó en una base local de pruebas (`smartcity_pruebas`) y se desplegó en **Azure Database for PostgreSQL Flexible Server**, base de datos `smartcity`. No es necesario ejecutar SQL de creación nuevamente sobre una base que ya contenga las tablas.

| Archivo | Función |
|---|---|
| [`01_schema.sql`](01_schema.sql) | Crea las ocho tablas, restricciones e integridad referencial. |
| [`verificar_esquema.sql`](verificar_esquema.sql) | Comprueba ocho tablas, ocho PK y seis FK. |
| [`pruebas_integridad.sql`](pruebas_integridad.sql) | Pruebas transaccionales de restricciones; verificadas **18/18** en local. |
| [`02_seed.sql`](02_seed.sql) | Inserta datos **DEMOSTRATIVOS**, reejecutable sin duplicados. |
| [`carga.py`](carga.py) | ETL de EPA AQS desde ZIP hacia PostgreSQL. |
| [`README_carga_epa.md`](README_carga_epa.md) | Manual técnico, políticas de datos y opciones de carga. |
| [`../docs/postgres/informes/carga_azure_500k.json`](../docs/postgres/informes/carga_azure_500k.json) | Evidencia JSON de la carga masiva en Azure. |
| [`../docs/postgres/diccionario_datos.md`](../docs/postgres/diccionario_datos.md) | Definiciones de las tablas y sus columnas. |

Para una **base vacía**, el orden es `01_schema.sql` → `verificar_esquema.sql` → `pruebas_integridad.sql` → `02_seed.sql` → `carga.py`. Las pruebas de integridad revierten sus propios registros de prueba; el seed y el ETL conservan sus inserciones. Ejecutar en una base nueva o previamente inspeccionada, nunca contra tablas de otro trabajo sin revisión.

### 2.2. Resultados finales comprobados

Los siguientes números fueron comprobados mediante consultas SQL sobre Azure, después de la carga masiva:

| Métrica en Azure | Valor |
|---|---:|
| Tablas / claves primarias / claves foráneas | **8 / 8 / 6** |
| Mediciones reales EPA AQS | **500.000** |
| Mediciones de demostración | **100** |
| Mediciones totales | **500.100** |
| Sensores EPA con mediciones | **1.528** |
| Sensores DEMO incluidos por el seed | **10** |
| Total esperado de sensores (EPA + DEMO) | **1.538** |
| Ubicaciones totales tras la carga masiva | **1.099** (1.096 antes + 3 nuevas) |
| Organismos responsables | **179** (sin nuevas altas reportadas en la carga masiva) |
| Mediciones sin sensor asociado | **0** |

La consulta final de Azure registró un intervalo `fecha_utc` entre **2025-01-01 00:00:00+00** y **2026-01-01 07:00:00+00**. El límite superior en enero de 2026 es compatible con el paso de horas locales de diciembre de 2025 a UTC.

La carga masiva de Azure seleccionó **250.000 filas PM2.5** (`88101`) y **250.000 PM10** (`81102`). Como ya existían 10.000 mediciones del primer muestreo distribuido, insertó **490.000 nuevas**, para un total de **500.000 EPA**. El informe se encuentra en [`carga_azure_500k.json`](../docs/postgres/informes/carga_azure_500k.json). El total local difiere porque se hicieron pruebas adicionales con otro modo de selección: **509.533 EPA** y **100 DEMO** (509.633 en total); no se debe confundir con la carga final de Azure.

### 2.3. Reproducción en Ubuntu 24.04

**Dependencia:**

```bash
sudo apt update
sudo apt install python3-psycopg2
```

**Preparar PostgreSQL local (solo si la base aún no existe):**

```bash
sudo -u postgres createdb smartcity_pruebas
sudo -u postgres psql -d smartcity_pruebas -v ON_ERROR_STOP=1 -f postgres/01_schema.sql
sudo -u postgres psql -d smartcity_pruebas -v ON_ERROR_STOP=1 -f postgres/verificar_esquema.sql
sudo -u postgres psql -d smartcity_pruebas -v ON_ERROR_STOP=1 -f postgres/pruebas_integridad.sql
sudo -u postgres psql -d smartcity_pruebas -v ON_ERROR_STOP=1 -f postgres/02_seed.sql
```

Estos comandos se ejecutan desde la **raíz del repositorio**. Si la base ya existe, omite `createdb` y revisa el estado del esquema antes de ejecutar `01_schema.sql`.

**Dataset EPA AQS, obtenido por separado (no incluido en GitHub):**

```text
aqs_sites.zip
aqs_monitors.zip
hourly_88101_2025.zip    # PM2.5, código 88101
hourly_81102_2025.zip    # PM10, código 81102
```

El directorio que se pase a `--datos` debe contener esos cuatro archivos. No se descargan ni descomprimen previamente: el ETL los lee por streaming dentro de los ZIP.

**Prueba local con muestreo distribuido:**

```bash
python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'host=127.0.0.1 port=5432 dbname=smartcity_pruebas user=postgres' \
  --por-archivo 5000 \
  --muestreo distribuida \
  --lote 1000 \
  --informe /tmp/smartcity_carga_local_10k.json
```

La ruta bajo `/home/dylan` es **un ejemplo del entorno de desarrollo** y se debe adaptar a cada equipo. La autenticación puede configurarse mediante `~/.pgpass` con permisos `chmod 600 ~/.pgpass`. Ejecutar Python como el usuario de Ubuntu que tiene lectura sobre los ZIP; no es necesario usar `sudo -u postgres` para el script.

**Carga de 500.000 filas en una base de prueba, tras validar la carga corta:**

```bash
python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'host=127.0.0.1 port=5432 dbname=smartcity_pruebas user=postgres' \
  --por-archivo 250000 \
  --muestreo distribuida \
  --lote 1000 \
  --informe /tmp/smartcity_carga_local_500k.json
```

**Azure (requiere acceso concedido al servidor, base y credenciales):**

```bash
python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'host=smartcity-postgres-tec.postgres.database.azure.com port=5432 dbname=smartcity user=smartcity_admin sslmode=require connect_timeout=30' \
  --por-archivo 250000 \
  --muestreo distribuida \
  --lote 1000 \
  --informe /tmp/smartcity_carga_azure_500k.json
```

> **No es necesario volver a ejecutar la carga contra Azure si ya tiene las 500.000 mediciones EPA.** La ejecución repetida con la misma selección no debe insertar nuevas mediciones. Nunca incluir contraseñas, `.pgpass`, `.env`, copias de la base ni los archivos ZIP grandes en Git.

### 2.4. Consultas de verificación

Ejecutar conectado a la base deseada (`smartcity` en Azure o `smartcity_pruebas` local):

```sql
SELECT
    COUNT(*) AS total_mediciones,
    COUNT(*) FILTER (WHERE fuente = 'EPA AQS hourly 2025') AS mediciones_epa,
    COUNT(DISTINCT id_sensor) FILTER
       (WHERE fuente = 'EPA AQS hourly 2025') AS sensores_epa,
    MIN(fecha_utc) AS primera_medicion,
    MAX(fecha_utc) AS ultima_medicion
FROM medicion;

SELECT COUNT(*) AS mediciones_sin_sensor
FROM medicion m
LEFT JOIN sensor s ON s.id_sensor = m.id_sensor
WHERE s.id_sensor IS NULL;

SELECT
    (SELECT COUNT(*) FROM sensor) AS sensores,
    (SELECT COUNT(*) FROM ubicacion) AS ubicaciones,
    (SELECT COUNT(*) FROM organismo_responsable) AS organismos;
```

El resultado observado en Azure fue **500.100 mediciones totales**, **500.000 EPA**, **1.528 sensores EPA con mediciones** y **0 mediciones sin sensor**. El conteo `MIN`/`MAX` de la primera consulta incluye las DEMO; para obtener fechas exclusivamente EPA se debe agregar `WHERE fuente = 'EPA AQS hourly 2025'` a la consulta correspondiente.

## 3. Trazabilidad, calidad y límites

- **Identificadores compartidos:** `id_ubicacion = EPA-{State Code}-{County Code}-{Site Number}` e `id_sensor = {id_ubicacion}-{Parameter Code}-{POC}`, preservando los ceros iniciales. MongoDB debe reutilizar esas cadenas como `zona_id` y `sensor_id` para facilitar el cruce lógico de datos; MongoDB **no comparte** las FK físicas de PostgreSQL.
- **Muestreo:** `primeras` elige las primeras N filas; `distribuida` selecciona N posiciones equiespaciadas en cada archivo de forma determinista. No es un muestreo aleatorio o estadísticamente representativo. Para 500.000 filas, el modo distribuido identifica 1.528 monitores.
- **Idempotencia:** el ETL asigna `id_medicion` BIGINT negativo mediante BLAKE2b de sensor, parámetro y timestamp UTC. Ante el mismo ID utiliza `ON CONFLICT DO NOTHING`. No compara el contenido de registros con el mismo ID y requiere revisión si se admiten observaciones múltiples por sensor y hora.
- **Estado e instalación:** `fecha_instalacion` se guarda `NULL` cuando no se conoce la instalación física. `estado` se deriva con un umbral fijo sobre `Last Sample Date` (>= 2025-10-01); **no equivale a una inspección del dispositivo**.
- **Agencia responsable:** prioridad `Collecting Agency > Reporting Agency > Owning Agency` según disponibilidad. Son roles diferentes en la fuente y se documenta esta simplificación.
- **Valores y calidad:** se conservan las mediciones negativas y aquellas con calificadores sin filtrarlas. En la selección masiva hubo **7.521 negativas** y **40.970 con calificador**. `Qualifier`, `Method Code` y unidad exacta de origen **no se guardan en la tabla `medicion`**; deben consultarse en los CSV originales.
- **Unidades:** PM2.5 usa en origen `Micrograms/cubic meter (LC)` y PM10 `Micrograms/cubic meter (25 C)`. La base almacena la unidad general `µg/m³` como unidad canónica sin conversión termodinámica; evitar equiparar las condiciones de referencia en análisis comparativos.
- **Integración de fuentes:** esta carga representa **EPA AQS**, un único repositorio oficial aunque se consuman cuatro archivos. El requisito de utilizar por lo menos dos fuentes de datos **no queda satisfecho solo con esta implementación**; se debe confirmar e integrar una segunda fuente con el equipo.
- **Seguridad:** el despliegue usa PostgreSQL en Azure y autenticación de base de datos. Si el firewall permite conexiones de cualquier IP, aumentan los intentos de acceso; mantener claves robustas, TLS y permisos mínimos. No publicar credenciales.
