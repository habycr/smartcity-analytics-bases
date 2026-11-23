# Fuentes de datos, ingestión y generación — SmartCity Analytics

**Estado:** carga EPA AQS 2025 implementada y verificada: 500.000 lecturas reales de PM2.5 y PM10. Se probó la repetición de carga y la conciliación de identificadores y ubicaciones con el catálogo compartido de PostgreSQL.

## Origen y alcance de los datos

La carga utilizada en este módulo procede de **EPA AQS AirData, año 2025**, mediante los archivos `hourly_88101_2025.zip` (PM2.5) y `hourly_81102_2025.zip` (PM10). Para los metadatos EPA se dispone también de `aqs_sites.zip` y `aqs_monitors.zip`. Estos cuatro ZIP pertenecen a **una sola fuente de origen: EPA AQS**; no se contabilizan como fuentes independientes.

Los CSV de prueba y los eventos, alertas e incidentes de demostración están identificados como **sintéticos**. Los archivos originales de gran tamaño se mantienen fuera de Git. La incorporación de una segunda fuente independiente corresponde a la integración general del proyecto.

## Reglas de transformación en `mongo/carga.py`

- Lectura streaming de CSV o ZIP que contenga CSV (no extraer masivamente los datos en memoria).
- Leer los códigos EPA como texto, conservar ceros iniciales, construir `zona_id=EPA-{State Code}-{County Code}-{Site Num}` y `sensor_id={zona_id}-{Parameter Code}-{POC}`.
- Aceptar solo los parámetros 88101 → `pm25` y 81102 → `pm10`.
- Usar `Date GMT` y `Time GMT`, no horas locales; MongoDB almacena BSON Date UTC en `fecha_utc`.
- Normalizar unidad a `µg/m³`; preservar la descripción de la unidad original en `procedencia.unidad_original`. El método no realiza ajuste termodinámico entre LC y 25 C.
- Conservar valores negativos y registrar calificadores del CSV si se encuentran; no construir calificadores para datos exportados de PostgreSQL si ya se perdieron.
- Usar `Decimal128` y precisión documentada de seis decimales, compatible con el almacenamiento `NUMERIC(18,6)` descrito para PostgreSQL.
- Rechazar filas cuya combinación `sensor_id`/`zona_id` no exista en el catálogo exportado del PostgreSQL del proyecto, informando cuántas fueron omitidas.
- Generar `_id` determinista. Cargar por lotes con `bulk_write`/`upsert` y `$setOnInsert`. Repetir el ETL no debe duplicar documentos; diferencias de valor para la misma clave no se sustituyen silenciosamente.

## Generación opcional

Si faltan registros para el objetivo, el argumento `--objetivo 500000` amplía las lecturas utilizando una semilla fija (3101), seleccionando lecturas de entrada y aplicando variaciones de ±2 % y desplazamientos de fechas. Las nuevas observaciones tienen `sintetico=true`, otra `fuente`, un `_id` reproducible y su referencia de origen. **No son datos EPA observados.** Debe reportarse cuántos documentos reales y sintéticos hay por separado.

## Validación, tamaños y evidencia

El ETL informa cantidad de filas leídas, registros aceptados, omitidos por catálogo, inválidos, insertados, ya existentes y sintéticos. Incluye conteo final y tamaño de documentos BSON de `lecturas`. Ese tamaño no sustituye por sí solo el cálculo de bytes del dataset completo ni demuestra procesamiento distribuido.

## Integración con PostgreSQL

Se empleó `postgres/datos_muestra/sensor.csv`, publicado en la rama del módulo PostgreSQL, como catálogo de los sensores EPA. La exportación equivalente desde PostgreSQL utiliza la consulta:

```sql
SELECT id_sensor, id_ubicacion
FROM public.sensor
WHERE id_sensor LIKE 'EPA-%'
ORDER BY id_sensor;
```

Se preparó `datos/reales/catalogo_postgres.csv` con las columnas `id_sensor,id_ubicacion` y se utilizó como argumento `--catalogo` en la carga y conciliación. El análisis de 500.000 lecturas devolvió 63 grupos y cero errores de correspondencia. Esta prueba no implica acceso directo a la base de Azure.

## Límites del conjunto implementado

Los datos almacenados en `lecturas` provienen de EPA AQS; la segunda fuente independiente requerida para el proyecto completo es un asunto de integración grupal. Las reglas de eventos y alertas son **ilustrativas, no normativas**. La conciliación comprobó referencias a sensores y zonas, no la igualdad fila por fila con PostgreSQL Azure. Las consultas Q01–Q10 y sus índices corresponden al responsable de consultas MongoDB.

## Comprobación automática de referencias

El script `mongo/conciliar_catalogo.py` compara grupos de `sensor_id`/`zona_id` en MongoDB contra el catálogo de PostgreSQL, excluyendo sintéticos por defecto. Comprueba unidad y tipo para variables de partículas. **No reemplaza** una conciliación fila a fila de las observaciones ni prueba equivalencia de conteos entre tecnologías.

## Resultados de la implementación en MongoDB

La carga de datos se realizó a partir de los archivos originales EPA AQS 2025, correspondientes a las mediciones horarias de PM2.5 y PM10.

Se utilizó Python 3.13 y PyMongo para procesar los archivos ZIP directamente, sin extracción manual. Los registros fueron transformados y almacenados en MongoDB 8.0 mediante operaciones de inserción condicional (`upsert`) por lotes de 1.000 documentos.

### Resultados de carga

| Indicador | Resultado |
|---|---:|
| Documentos reales cargados | 500.000 |
| Mediciones PM2.5 | 250.000 |
| Mediciones PM10 | 250.000 |
| Documentos sintéticos en lecturas | 0 |
| Filas inválidas reportadas | 0 |
| Duplicados evitados en las cargas masivas | 2.000 |
| Tamaño BSON reportado de lecturas | 192.946.993 bytes |

La carga se ejecutó de manera incremental. Primero se importaron 1.000 registros de cada variable y posteriormente se ampliaron ambos conjuntos hasta alcanzar 250.000 registros por variable.

El proceso identificó los registros previamente existentes, evitando duplicarlos durante las ejecuciones posteriores.

### Conciliación de identificadores

Se ejecutó el script `mongo/conciliar_catalogo.py` utilizando el catálogo de sensores y ubicaciones compartido por PostgreSQL.

Los resultados fueron:

- Documentos revisados: 500.000.
- Grupos evaluados: 63.
- Errores detectados: 0.

Esta prueba permitió verificar la correspondencia de identificadores de sensores y ubicaciones con el catálogo utilizado. No constituye una conciliación individual de cada medición con PostgreSQL Azure.

### Eventos, alertas e incidentes

Se generaron documentos simulados con fines académicos:

- Eventos: 10.
- Alertas: 10.
- Incidentes: 3.

Estos documentos se identificaron como sintéticos y se construyeron mediante reglas ilustrativas aplicadas a las lecturas. No representan alertas oficiales ni incidentes confirmados por EPA.

El proceso se ejecutó dos veces y conservó las mismas cantidades, demostrando que no acumula documentos al repetirse.

### Evidencias generadas

- `docs/reporte_epa_pm25_250k.json`
- `docs/reporte_epa_pm10_250k.json`
- `mongo/pruebas/conteos.js`
- `mongo/pruebas/validadores.js`
- `mongo/03_crud.js`
- `mongo/conciliar_catalogo.py`

### Alcance de la entrega

La implementación de este módulo cubre modelo, validadores, carga de 500.000 lecturas reales EPA, simulaciones identificadas, CRUD y pruebas de integridad con el catálogo compartido. Las consultas analíticas e índices se implementan en el módulo MongoDB de consultas del equipo.