# Evidencia del primer bloque S01

Fecha: 9 de noviembre de 2026 (America/Costa_Rica).
Identificador de esta validación: `s01-muestra-v1-20261109`.
Base Git: `8dfeb24df72f3f934b2afa76fe38ac37748b0fce`, rama
`feature/sprint2-spark-consultas`; cambios todavía sin commit.

## Entorno ejecutado

- Ubuntu x86_64; Python 3.12.3.
- Entorno aislado `/tmp/smartcity-spark-venv`: PySpark 4.0.1, Py4J 0.10.9.9.
- Temurin OpenJDK 17.0.21+9, extraído en `/tmp/smartcity-jdk17`.
- Spark `local[2]`, sesión UTC, ANSI habilitado, dos particiones de shuffle
  en las pruebas. Sin MongoDB, PostgreSQL ni HDFS.
- Muestra fija de ocho lecturas, enteramente sintética.
  SHA-256 de `spark/datos_muestra/lecturas_sinteticas.jsonl`:
  `0492558b5e325d445b5cfea6440c6d3814e6d65d8bd4eb27f618ad2126287b10`.
- SHA-256 del JDK descargado (tar.gz):
  `8b9b611d917e3dfd8419d3566b5949226f69b052fed7e109c1368add1dfe8711`.

Python estaba disponible al inicio; Java y PySpark no. Se descargaron en
`/tmp` sin modificar las dependencias o el entorno del sprint 1. La descarga
necesitó acceso de red autorizado fuera del sandbox.

## Pruebas ejecutadas

Desde la raíz del repositorio:

```bash
JAVA_HOME=/tmp/smartcity-jdk17 \
PYSPARK_PYTHON=/tmp/smartcity-spark-venv/bin/python \
SPARK_LOCAL_IP=127.0.0.1 \
/tmp/smartcity-spark-venv/bin/python -m unittest discover \
  -s spark/pruebas -p 'test_*.py' -v
```

Resultado real, código de salida **0**:

```text
Ran 18 tests in 37.112s

OK
```

Cobertura ejecutada:

| Casos | Resultado |
|---|---|
| Conteos 3/3/2 y empates tras reparticionar a 1 y 3 particiones | OK |
| Inicio incluido, fin excluido y microsegundos próximos a ambos | OK |
| Límites independientes y offsets equivalentes a UTC | OK |
| Zona exacta, filtros combinados y zona inexistente | OK |
| Todos / observados / sintéticos, con etiquetas mixtas solo en memoria | OK |
| DataFrame vacío con esquema y período sin lecturas | OK |
| Duplicado idéntico contado como una fila adicional | OK |
| Ausencia de cada una de las diez columnas obligatorias | OK |
| Tipos incorrectos, columnas repetidas y sesión distinta de UTC | OK |
| Nulos en cada columna, incluso fuera de un filtro sin coincidencias | OK |
| Cadenas vacías o de solo espacios en cada campo string | OK |
| Parámetros inválidos, fechas sin zona y rangos invertidos/iguales | OK |
| Decimal exacto, signo negativo y muestra marcada como sintética | OK |
| Lectura y escritura de Parquet temporal; JSONL vacío | OK |
| Exceso de escala/precisión, NaN, null, fecha sin zona e imposible | OK |

El primer intento bajo sandbox terminó con código 5, **0 pruebas ejecutadas**:
el gateway Java no pudo abrir su socket (`Operation not permitted`,
`JAVA_GATEWAY_EXITED`). No fue una aprobación. El resultado OK anterior
corresponde a la ejecución posterior autorizada con sockets locales.

Se observaron avisos de módulos incubadores de Java, ausencia de biblioteca
nativa Hadoop (Spark utilizó clases Java) y `ResourceWarning` por sockets
durante `collect()` en PySpark. No se ocultaron. La batería terminó en OK;
estos avisos no acreditan una validación de recursos bajo carga sostenida.
Log local completo: `/tmp/smartcity-s01-tests-local.log` (temporal).

También se ejecutaron con éxito:

- `python3 -m compileall -q spark`: sintaxis válida.
- `/tmp/smartcity-spark-venv/bin/python -m pip check`: `No broken requirements found`.
- `/tmp/smartcity-spark-venv/bin/python -m spark.cli --help`: código 0.
- `git diff --check`: sin errores de espacios.

## Terminal

Con las variables y dependencias del [README](../README.md), se ejecutó:

```bash
/tmp/smartcity-spark-venv/bin/python -m spark.cli \
  --entrada spark/datos_muestra/lecturas_sinteticas.jsonl --formato jsonl
```

Código 0; salida real:

```text
+---------+-----------------+
|sensor_id|cantidad_lecturas|
+---------+-----------------+
|DEMO-SA  |3                |
|DEMO-SB  |3                |
|DEMO-SC  |2                |
+---------+-----------------+
```

Log local: `/tmp/smartcity-s01-cli.log`.

También se ejecutó con código 0:

```bash
/tmp/smartcity-spark-venv/bin/python -m spark.cli \
  --entrada spark/datos_muestra/lecturas_sinteticas.jsonl --formato jsonl \
  --desde 2025-01-01T00:00:00Z --hasta 2025-01-02T00:00:00Z \
  --zona-id DEMO-Z1 --datos sinteticos
```

Salida real: `DEMO-SA=2`, `DEMO-SC=1`, en ese orden.
Log local: `/tmp/smartcity-s01-cli-filtrada.log`.

## Límites

No se ejecutaron pruebas contra servicios, pruebas históricas del sprint 1,
benchmark, escenarios distribuidos físicos ni carga de un millón de registros.
No se declaran aprobados. Esta evidencia cubre únicamente la muestra y los
casos sintéticos descritos. Instalación y reproducción: [README](../README.md).
