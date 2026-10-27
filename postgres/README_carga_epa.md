# Carga EPA AQS a PostgreSQL

## Alcance

`carga.py` lee directamente cuatro ZIP de EPA AQS: catálogos `aqs_sites.zip`, `aqs_monitors.zip` y mediciones horarias `hourly_88101_2025.zip` (PM2.5), `hourly_81102_2025.zip` (PM10). Requiere las **ocho tablas ya creadas** mediante `01_schema.sql`.

No altera tablas existentes, no modifica `usuario`, no descarga datos, y utiliza identificadores `EPA-...` compartibles con `sensor_id` y `zona_id` en MongoDB. Inserta únicamente los monitores necesarios para el subconjunto seleccionado. Conserva los datos `DEMO-...` del `02_seed.sql`.

## Preparación Ubuntu 24.04

Desde tu repositorio:

```bash
sudo apt update
sudo apt install python3-psycopg2
```

Si ejecutas el ETL como el usuario PostgreSQL del sistema para aprovechar la autenticación *peer*, ejecuta:

```bash
cd ~/Bases/smartcity-analytics-bases
sudo -u postgres python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'dbname=smartcity_pruebas user=postgres' \
  --por-archivo 5000 \
  --informe /tmp/smartcity_carga_epa_10k.json
```

**Atención:** si el usuario `postgres` no puede leer `/home/dylan/.../epa`, copia los ZIP a un directorio con permisos de lectura específicos para `postgres`, o configura autenticación por contraseña para ejecutar el script como tu propio usuario. No cambies indiscriminadamente los permisos de tu carpeta personal.

**Dos modos de selección:** `--muestreo primeras` (predeterminado) mantiene exactamente el comportamiento anterior: las primeras N filas por ZIP. `--muestreo distribuida` cuenta previamente las filas de cada ZIP y selecciona hasta N posiciones **equiespaciadas a lo largo de todo el CSV**, `floor(k*T/N)`, para `k=0...N-1`, donde T es el total de filas del archivo. Esto distribuye la muestra por el orden del CSV, permite incluir más monitores y conserva la selección al repetir la ejecución. **No es un muestreo aleatorio, uniforme por sensor ni una garantía de representatividad geográfica**. Dado que recorre los ZIP completos para contar y seleccionar, requiere más lectura de disco/CPU que `primeras`, sin extraer archivos ni cargarlos completos a RAM.

Prueba distribuida de hasta 10.000 filas (5.000 por archivo):

```bash
python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'host=127.0.0.1 port=5432 dbname=smartcity_pruebas user=postgres' \
  --por-archivo 5000 \
  --muestreo distribuida \
  --informe /tmp/smartcity_carga_epa_distribuida.json
```

Usa las credenciales locales ya configuradas en `~/.pgpass`; no incluyas contraseñas en el comando. El informe incluye `modo_muestreo`, las cantidades de filas por archivo en modo distribuido y el número de sensores/ubicaciones efectivamente insertados. Los datos anteriores permanecen en la base y las mediciones iguales se omiten mediante IDs deterministas.

Cuando la prueba resulte correcta, puedes subir el límite a 250.000 por archivo (hasta 500.000 lecturas). Para mantener la estrategia distribuida, agrega `--muestreo distribuida`:

```bash
sudo -u postgres python3 postgres/carga.py \
  --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn 'dbname=smartcity_pruebas user=postgres' \
  --por-archivo 250000 \
  --muestreo distribuida \
  --informe /tmp/smartcity_carga_epa_500k.json
```

Al subir el límite en **modo primeras**, los primeros registros ya cargados se omiten por PK estable; en **modo distribuida**, cambiar N puede producir un conjunto de posiciones diferente, por lo que no necesariamente incluye toda la muestra distribuida anterior. En ambos modos, los IDs de mediciones coincidentes se omiten por PK estable. Así, el número de **registros nuevos** será menor que el número de filas procesadas. Todo el trabajo de una ejecución se confirma con un único COMMIT; ante error se revierte. Para 500.000 filas, el script puede requerir cierto tiempo por red y servidor.

### Uso en Azure (solo tras validar localmente)

El `--dsn` acepta los parámetros habituales de libpq; evita contraseñas en el historial de la terminal. Configura credenciales mediante archivo `.pgpass` con permisos 0600 o variables de entorno `PGPASSWORD`, `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` y `PGSSLMODE=require`.

```bash
# Ejemplo: tras exportar PGHOST, PGUSER, PGDATABASE y PGSSLMODE
python3 postgres/carga.py --datos /home/dylan/Bases/smartcity-datasets/epa \
  --dsn '' --por-archivo 5000 --informe /tmp/smartcity_carga_epa_azure.json
```

**No subas archivos `.env`, `.pgpass` o contraseñas al repositorio.** Antes de cargar en Azure, coordina con Fabio qué datos e índices necesita para sus consultas.

## Decisiones y límites de calidad

- `id_ubicacion = EPA-{State Code}-{County Code}-{Site Number}`; `id_sensor = {id_ubicacion}-{Parameter Code}-{POC}`. Se conservan ceros iniciales.
- `fecha_instalacion = NULL`: EPA informa primer año de datos, no instalación exacta.
- `estado` es una **etiqueta derivada**, no estado físico: `activo` si `Last Sample Date >= 2025-10-01`, en otro caso `inactivo`. Fecha de referencia fija para reproducibilidad.
- Organismo: `Collecting Agency`, si falta `Reporting Agency`, si falta `Owning Agency` de la estación. Se mantienen vacíos los datos de contacto no disponibles. **El rol de cada organismo puede diferir**; la transformación no implica equivalencia de responsabilidades.
- Si no existe un organismo verificable, o la estación tiene coordenadas inválidas, se excluye el monitor de esta carga. Se informan los descartes.
- Nombre de sitio ausente: se genera `Estación EPA ... (nombre generado)`; `distrito` corresponde a `County Name`, no a un distrito de Costa Rica.
- Se almacenan `pm25`, `pm10` en `µg/m³` como unidad canónica de concentración. Los originales usan **condiciones de referencia diferentes**: `(LC)` y `(25 C)`. El proceso NO realiza conversiones termodinámicas ni presupone que ambas condiciones sean equivalentes; la distinción queda en el informe y en los ZIP crudos. Deben separarse en los análisis y revisar si el modelo debe ampliarse para conservar esta diferencia por observación.
- Conserva valores negativos y valores con `Qualifier` sin aplicar filtros: aún no existe una política de calidad EPA aprobada. `Qualifier`, `Method Code`, `MDL` y unidad original **no se almacenan** en las ocho tablas actuales y deben preservarse en los ZIP originales.
- `id_medicion` es BIGINT **negativo** determinista mediante BLAKE2b de (sensor, parámetro, fecha UTC); por convenio, IDs positivos quedan para datos sintéticos y `IDENTITY`. Los conflictos de la misma PK se omiten; las colisiones criptográficas son extraordinariamente improbables, pero no se verifica individualmente que cada registro existente sea idéntico. Si se requieren versiones o lecturas múltiples para la misma hora, habrá que revisar la clave.
- Este proceso cubre **solo EPA**; CityPulse sigue siendo segunda fuente pendiente de integrar. No identifica sensores sin actividad de otras redes, ni garantiza representación uniforme de todas las regiones.

## Verificación SQL

```sql
SELECT COUNT(*) AS sensores_epa FROM public.sensor WHERE id_sensor LIKE 'EPA-%';
SELECT COUNT(*) AS ubicaciones_epa FROM public.ubicacion WHERE id_ubicacion LIKE 'EPA-%';
SELECT COUNT(*) AS mediciones_epa FROM public.medicion WHERE fuente = 'EPA AQS hourly 2025';
SELECT COUNT(*) AS mediciones_demo FROM public.medicion WHERE fuente LIKE 'DEMO%';
SELECT nombre_variable, unidad_canonica FROM public.variable_medicion WHERE nombre_variable IN ('pm25','pm10');
```

Repite el ETL con los mismos argumentos y verifica `mediciones_insertadas: 0` en el JSON. Los archivos horarios no se alteran.
