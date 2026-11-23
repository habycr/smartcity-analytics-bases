# Spark: base mínima y S01

Primer bloque de Javier, sprint 2. Incluye únicamente el análisis descriptivo
S01 («Sensores que generan más información»): información significa **cantidad
de lecturas**, no bytes ni estado físico del sensor. No incluye ETL de fuentes
crudas, conectores, Hadoop, dashboard, benchmark ni otras consultas.

## Base y alcance documental

Rama: `feature/sprint2-spark-consultas`, creada desde `origin/development`
después de `git fetch origin`, en
`8dfeb24df72f3f934b2afa76fe38ac37748b0fce`.
La rama inicial era `development`, sin diferencias rastreadas. Existían tres
PNG sin seguimiento en `docs/informe_sprint1/figuras/`, conservados.
No se encontraron instrucciones `AGENTS.md` aplicables.

Se leyeron el enunciado oficial `CE3101_Enunciado_Proyecto_II_Semestre_2026.pdf`
(28 páginas) y `Division_Sprint2_SmartCity-1.pdf` (11 páginas) antes de implementar.
No se encontró una contradicción que afecte S01: enunciado p. 16 y división
pp. 5/7 coinciden. El enunciado prevalece. La división propone Hive, carpetas,
calendario intermedio y responsabilidades; no son exigencias del profesor.
El enunciado permite MapReduce o Hive, y exige al menos 1.000.000 de registros
procesados por Spark (p. 26), dos fuentes y mínimo 100 MB de dataset (pp. 6/7).
Esta muestra de ocho filas **no acredita esos requisitos**, distribución física
ni rendimiento. Tampoco pretende cubrir todavía todos los análisis de p. 15.
La diferencia entre la sección de atributos y la rúbrica del propio enunciado
queda fuera de este bloque; la división ya señala ambas formulaciones.

Se reutilizaron los significados de
[contrato MongoDB](../docs/contrato_mongo.md),
[contrato compartido](../docs/postgres/contrato_datos.md) y
[carga documental](../mongo/carga.py).
MongoDB Q01 y PostgreSQL Q01 tienen otras semánticas: **S01 no las reemplaza**.
Los responsables históricos de esos contratos corresponden al sprint 1;
la asignación del sprint 2 es la indicada en la división y en la solicitud.

## Propuesta de integración de entrada v1

**Propuesta de Javier para coordinar con Edward y Dylan; no es un acuerdo
aprobado por todo el equipo.** No crea ni sustituye el futuro contrato común
`docs/contrato_sprint2.md`, cuya preparación pertenece a Dylan/Edward.

Edward entregaría una instantánea curated de lecturas con estos campos,
representada por un DataFrame o por Parquet. JSONL normalizado sirve también
para intercambio pequeño y pruebas sin bases de datos. Esquema explícito en
[contrato.py](contrato.py); los campos adicionales no participan en S01.

| Campo obligatorio | Tipo Spark | Significado / representación JSONL |
|---|---|---|
| `lectura_id` | string | Identificador de la observación con espacio de nombres de origen |
| `sensor_id` | string | Exactamente `sensor.id_sensor`; conserva ceros y guiones |
| `zona_id` | string | Exactamente `ubicacion.id_ubicacion` |
| `tipo_sensor` | string | Clasificación existente; EPA usa `particulas` |
| `variable` | string | Magnitud canónica existente, p. ej. `pm25` |
| `valor` | decimal(18,6) | Decimal exacto con signo; JSONL usa texto decimal |
| `unidad` | string | Unidad canónica existente, p. ej. `µg/m³` |
| `fecha_utc` | timestamp (LTZ) | Instante UTC; JSONL `YYYY-MM-DDTHH:mm:ss[.ffffff]Z` |
| `fuente` | string | Procedencia original, sin convertir una simulación en fuente real |
| `sintetico` | boolean | `true` generado, `false` observado; JSONL booleano nativo |

Todos son obligatorios incluso si S01 no opera directamente con `valor` o
`unidad`. Se rechazan columnas faltantes, nombres repetidos, tipos distintos,
nulos y cadenas vacías o de solo espacios. No se convierten automáticamente
tipos de un DataFrame ni se recortan identificadores. El indicador `nullable`
del esquema permite detectar y rechazar nulos; no autoriza ausencias.
La validación revisa **toda la entrada antes de los filtros** y ejecuta una
acción Spark, retornando solo un conteo escalar. No recoge el dataset en Python.

Mapeo propuesto de `lectura_id`, a implementar por el exportador de Edward:

- MongoDB: `mongo:<base>.<coleccion>:string:<_id literal>` para IDs cadena
  (incluidos los `SC-…` de `mongo/carga.py`), o
  `mongo:<base>.<coleccion>:objectid:<hexadecimal>` para ObjectId.
  Otros tipos BSON requieren definir un encoding tipado antes de exportar.
- PostgreSQL: `postgres:<esquema>.<tabla>:bigint:<id_medicion decimal con signo>`.
  Los BIGINT negativos deterministas se conservan como texto, nunca float.
- La muestra usa `muestra:DEMO-L001` a `muestra:DEMO-L008`.

No se equiparan `_id` de MongoDB e `id_medicion`. Una exportación de la misma
observación desde ambos motores **no se puede concatenar sin conciliación**:
serían dos filas para S01. Coordinar snapshot, espacio de nombres estable,
revisiones y solapamiento con Edward. No se derivan IDs del número de fila.

Decimal128 BSON se exportaría a texto decimal exacto y después a
`DecimalType(18,6)`; `NUMERIC(18,6)` de PostgreSQL se conservaría en ese mismo
tipo. La compatibilidad es con el subconjunto representable: Decimal128 puede
superar esa precisión. JSONL acepta hasta 12 dígitos enteros y 6 fraccionarios,
sin exponente, `NaN`, infinito ni redondeo. Una precisión mayor exige acordar
otro tipo, no truncar datos. No hay paso por `float`/`double`.
Se conservan negativos, ceros, variables y unidades; S01 no aplica reglas de
calidad ambientales ni mezcla valores para promediarlos. La unidad canónica
EPA no elimina la diferencia de condiciones de referencia LC/25 C del contrato.

El ETL convertiría BSON Date o TIMESTAMPTZ al mismo instante en Parquet
`TimestampType` con sesión UTC; `TimestampNTZType` se rechaza. JSONL requiere
`Z` y hasta microsegundos; fechas imposibles terminan en error de validación.
No se acepta `mongoexport` Extended JSON sin normalizar (`$date`,
`$numberDecimal`, `$oid`): esta capa no es un conector ni el ETL de Edward.
Parquet usa los tipos almacenados, sin imponer un esquema que oculte campos
faltantes. JSONL usa esquema explícito y modo `FAILFAST` para errores de parseo;
los campos omitidos quedan nulos y S01 los rechaza en entradas no vacías.

**Duplicados:** S01 aplica semántica de filas (`COUNT(*)`). Toda repetición,
incluido un `lectura_id` repetido o una fila idéntica, aumenta el conteo.
No comprueba unicidad, no deduplica ni elige una revisión. El ETL debe reportar
y resolver duplicados de forma acordada antes de publicar curated. Este
comportamiento se prueba expresamente. No se corrigen nulos ni se imputan datos.

## Función y salida

```python
from spark.consultas.S01 import sensores_mas_informacion

resultado = sensores_mas_informacion(
    lecturas,  # DataFrame con el contrato anterior, sesión UTC
    desde="2025-01-01T00:00:00Z",
    hasta="2025-01-02T00:00:00Z",
    zona_id=None,
    sintetico=None,
)
```

`desde` es inclusivo y `hasta` exclusivo. Cada límite es opcional; si ambos
existen se exige `desde < hasta`. Se admiten strings ISO con zona explícita o
`datetime` consciente de zona; offsets se normalizan al mismo instante UTC.
No se asume la zona del equipo para fechas sin zona.
`zona_id` compara texto exacto. `sintetico=None` incluye todos, `False` solo
observados, `True` solo generados. Todos los filtros se combinan con AND.
Sin filtros se incluyen todas las fechas, zonas, variables, fuentes y marcas.

| Columna de salida | Tipo | Semántica |
|---|---|---|
| `sensor_id` | string | Sensor con al menos una fila seleccionada |
| `cantidad_lecturas` | long | Total de filas seleccionadas para el sensor |

Orden global: `cantidad_lecturas DESC, sensor_id ASC` (comparación binaria
predeterminada de strings Spark). La entrada vacía conserva este esquema y
produce cero filas; no inventa sensores con conteo cero. El agregado es
perezoso después de la validación. No inicia sesiones ni lee archivos.
La CLI muestra un número acotado de resultados; `--limite` no reduce la entrada.
La salida mínima no añade columnas ambiguas de unidad o fuente cuando el
conteo combina varias: Fabio debe conservar los filtros y el snapshot junto
con el resultado. Persistencia, `run_id` y metadatos comunes se coordinarán
antes de la integración de publicación, sin implementar ahora ese bloque.

## Reproducir en Ubuntu sin cambios globales

Combinación elegida: Python **3.12**, PySpark **4.0.1**, Py4J **0.10.9.9**,
Java **17**. [Instalación oficial de PySpark 4.0.1](https://spark.apache.org/docs/4.0.1/api/python/getting_started/install.html)
documenta Python >=3.9 y Java >=17. Se usa la API DataFrame sobre JVM sin
pandas, Arrow, Spark Connect ni UDF Python. Las dependencias del sprint 1 en
`../requirements.txt` y su `.venv` permanecen intactas.

Desde la raíz del repositorio, en Ubuntu x86_64 con Python 3.12 y soporte venv:

```bash
python3 --version
python3 -m venv /tmp/smartcity-spark-venv
/tmp/smartcity-spark-venv/bin/python -m pip install -r spark/requirements.txt

# Solo si no tienes un JDK 17 local. Descarga oficial, sin sudo ni instalación global.
curl --fail --location --retry 2 --output /tmp/smartcity-jdk17.tar.gz \
  'https://api.adoptium.net/v3/binary/latest/17/ga/linux/x64/jdk/hotspot/normal/eclipse'
mkdir -p /tmp/smartcity-jdk17
tar -xzf /tmp/smartcity-jdk17.tar.gz -C /tmp/smartcity-jdk17 --strip-components=1
export JAVA_HOME=/tmp/smartcity-jdk17
export PATH="$JAVA_HOME/bin:$PATH"
export PYSPARK_PYTHON=/tmp/smartcity-spark-venv/bin/python
export SPARK_LOCAL_IP=127.0.0.1
java -version

/tmp/smartcity-spark-venv/bin/python -m unittest discover -s spark/pruebas -p 'test_*.py' -v

/tmp/smartcity-spark-venv/bin/python -m spark.cli \
  --entrada spark/datos_muestra/lecturas_sinteticas.jsonl --formato jsonl

/tmp/smartcity-spark-venv/bin/python -m spark.cli \
  --entrada spark/datos_muestra/lecturas_sinteticas.jsonl --formato jsonl \
  --desde 2025-01-01T00:00:00Z --hasta 2025-01-02T00:00:00Z \
  --zona-id DEMO-Z1 --datos sinteticos
```

Si falta soporte venv, se requiere `python3.12-venv` del administrador de
Ubuntu, o una distribución local de Python equivalente; no se instala aquí.
Si falta Java/PySpark, ejecutar las líneas anteriores de descarga/instalación.
No reutilizar un `SPARK_HOME` de otra versión. En ARM64 adaptar la descarga
del JDK a `aarch64`. El endpoint `latest/17` selecciona un parche actual;
la versión realmente probada se registra en [evidencia](pruebas/RESULTADOS.md).

Resultados de muestra sin filtros: `DEMO-SA=3`, `DEMO-SB=3`, `DEMO-SC=2`.
Segundo ejemplo filtrado: `DEMO-SA=2`, `DEMO-SC=1`.
Las ocho filas son fijas, sin aleatoriedad, totalmente inventadas, con prefijos
`DEMO-`, fuente `SIMULACION prueba unitaria S01 v1` y `sintetico=true`.
Las pruebas de datos mixtos cambian etiquetas solo en memoria; no acreditan
observaciones reales. Las pruebas históricas del sprint 1 no se modifican.

## Coordinación pendiente

- **Edward:** aprobar/revisar esta propuesta, representación del ID y decimal,
  normalización UTC, política de nulos/duplicados/revisiones, reporte de calidad,
  snapshot y manifiesto (origen, licencia, conteos, bytes y marca sintética).
  Entregar Parquet curated y una muestra del ETL real con este esquema;
  verificar referencias contra los catálogos y evitar doble exportación.
- **Dylan:** coordinar Python/Java/Spark con Hadoop/Hive, URI y rutas curated,
  permisos y particiones HDFS, configuración cliente, catálogos y snapshot.
  La ejecución local no valida HDFS ni compatibilidad con su despliegue.
- La muestra no cambia las responsabilidades de ingestión o almacenamiento.
  El millón de registros, benchmark comparable y publicación para Fabio
  requieren una fase posterior con los datos y servicios del equipo.
