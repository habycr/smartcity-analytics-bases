# Muestra portátil de EPA AQS — SmartCity Analytics

Esta carpeta contiene el generador e importador de una **muestra real**, extraída de las mediciones EPA AQS 2025 que ya se cargaron en PostgreSQL. Los CSV **se generan en tu máquina**; no se inventan valores ni se requieren los ZIP de EPA para importar la muestra después de generarla.

## Archivos generados

`categoria_sensor.csv`, `tipo_sensor.csv`, `organismo_responsable.csv`, `ubicacion.csv`, `variable_medicion.csv`, `sensor.csv`, `medicion.csv` y `manifest.json`. Las tablas `usuario` y sus datos no se incluyen porque no están relacionados con las mediciones EPA; tras importar quedarán vacíos.

Se incluyen **siete tablas** porque los tres CSV principales (`ubicacion`, `sensor`, `medicion`) no se pueden importar en una BD vacía sin sus catálogos y organismos relacionados. Los IDs exportados son los mismos de la BD original.

## Requisitos

- PostgreSQL 16 y `psycopg2` (`sudo apt install python3-psycopg2`).
- Base origen `smartcity_pruebas` con EPA AQS ya cargado.
- Archivo privado `~/.pgpass` con la contraseña local; nunca incluir contraseñas en Git.

## 1. Exportar una muestra real (3000 mediciones EPA)

Desde la raíz del repositorio:

```bash
python3 postgres/datos_muestra/muestra.py exportar \
  --dsn 'host=127.0.0.1 port=5432 dbname=smartcity_pruebas user=postgres' \
  --directorio postgres/datos_muestra \
  --max-mediciones 3000
```

Las 3000 mediciones se distribuyen entre sensores mediante una selección determinista: primero una lectura por sensor, luego la segunda de cada sensor, etc.; las filas se ordenan por fecha e ID. **No es una muestra aleatoria ni estadísticamente representativa**. El exportador selecciona primero las mediciones, luego exporta exclusivamente los sensores, ubicaciones, organismos, tipos, categorías y variables necesarios para conservar todas las claves foráneas. Consulta `manifest.json` para conteos y sumas SHA-256.

## 2. Reproducir en una base limpia

**No ejecutar en `smartcity_pruebas` ni en Azure.** Crea una base temporal nueva; el script de importación rechaza tablas con filas:

```bash
sudo -u postgres createdb smartcity_muestra
sudo -u postgres psql -v ON_ERROR_STOP=1 -d smartcity_muestra -f postgres/01_schema.sql
```

Si tu usuario local `postgres` se autentica por TCP mediante `~/.pgpass`:

```bash
python3 postgres/datos_muestra/muestra.py importar \
  --dsn 'host=127.0.0.1 port=5432 dbname=smartcity_muestra user=postgres' \
  --directorio postgres/datos_muestra
```

El importador usa una sola transacción y verifica que no existan mediciones sin sensor. Los CSV se importan en orden de dependencias, preservando las claves primarias. La muestra **no necesita** ejecutar `02_seed.sql`.

## 3. Verificar

```bash
sudo -u postgres psql -d smartcity_muestra -c 'SELECT COUNT(*) FROM medicion;'
sudo -u postgres psql -d smartcity_muestra -f postgres/verificar_esquema.sql
```

El total de `medicion` debe coincidir con `manifest.json` (normalmente 3000), y `verificar_esquema.sql` debe validar las ocho tablas y las relaciones.

## Límites y convenciones

- Solo se exportan filas con `fuente = 'EPA AQS hourly 2025'` e identificador de sensor `EPA-%`.
- Las fechas se exportan en UTC desde una sesión con `TIME ZONE 'UTC'`.
- Los negativos EPA se conservan y los calificadores no están en el esquema relacional; permanecen en el ZIP original.
- Los nombres y las unidades se heredan de los registros ya cargados.
- El conjunto pequeño es demostrativo, no sustituye la carga completa de 500.000 mediciones.
- Los CSV contienen datos públicos EPA; confirma licencias y procedencia antes de redistribuir.
