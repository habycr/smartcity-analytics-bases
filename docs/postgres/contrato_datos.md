# SmartCity Analytics — Contrato de datos PostgreSQL ↔ MongoDB

**Estado:** implementación integrada en development. Se verificaron las consultas MongoDB y la conciliación contra el catálogo exportado de PostgreSQL en Ubuntu. No implica aprobación formal de todo el equipo.

**Alcance:** datos EPA AQS 2025 de calidad del aire (PM2.5 y PM10). Los identificadores `DEMO-` corresponden a ejemplos sintéticos.

## 1. Propósito y fuentes de verdad

- **PostgreSQL:** fuente de verdad para los catálogos relacionales: `sensor`, `ubicacion`, `tipo_sensor`, `categoria_sensor`, `organismo_responsable`, `variable_medicion` y las mediciones cargadas por el ETL.
- **MongoDB:** almacenamiento documental de lecturas para los flujos asignados al equipo MongoDB. Los documentos deben **referenciar** los identificadores de PostgreSQL, no inventar una numeración distinta para los mismos sensores o ubicaciones.
- **No existe una clave foránea automática entre motores:** la integridad cruzada debe verificarse con consultas/scripts de conciliación.
- Los cuatro ZIP usados en este ETL proceden de **EPA AQS** y, por sí solos, **no constituyen dos repositorios de origen**. La incorporación y homologación de una segunda fuente continúa pendiente de coordinación.

## 2. Identificadores compartidos

Los componentes de EPA se toman **como texto**, conservando los ceros iniciales y el valor original del CSV.

| Concepto | PostgreSQL | MongoDB | Regla |
|---|---|---|---|
| Estación / ubicación EPA | `ubicacion.id_ubicacion` (`VARCHAR(64)`) | `zona_id` (`string`) | `EPA-{State Code}-{County Code}-{Site Number}` |
| Monitor / sensor EPA | `sensor.id_sensor` (`VARCHAR(64)`) | `sensor_id` (`string`) | `{zona_id}-{Parameter Code}-{POC}` |
| Tipo de sensor | `sensor.tipo_sensor` (`VARCHAR(80)`) | `tipo_sensor` (`string`) | Para estos archivos, `particulas` |
| Variable medida | `variable_medicion.nombre_variable` | `variable` (`string`) | `pm25` o `pm10` |
| Origen | `medicion.fuente` | `fuente` (`string`) | Para estas filas: `EPA AQS hourly 2025` |

**Ejemplo ilustrativo de formato** (no certifica que este monitor esté en el subconjunto cargado):

```text
zona_id   = EPA-01-003-0010
sensor_id = EPA-01-003-0010-88101-3
```

**Reglas obligatorias de coincidencia:**

1. `sensor_id` coincide **exactamente**, incluidos guiones y ceros iniciales, con `sensor.id_sensor`.
2. `zona_id` coincide con `ubicacion.id_ubicacion` y con la ubicación asignada al sensor en PostgreSQL.
3. Un sensor EPA tiene una sola `zona_id` en el catálogo actual. No se infiere una ubicación distinta a partir de las coordenadas de una lectura.
4. No se reutiliza `sensor_id` para otros parámetros o POC; el código del parámetro y POC son parte de la identidad.
5. Los identificadores sintéticos de prueba mantienen el prefijo `DEMO-`; se identifican además mediante el campo documental `sintetico`. **No se deduce que todos los ID fuera de `DEMO-` sean EPA** si se añade otra fuente.

## 3. Contrato implementado para documentos de lecturas

**Colección implementada:** `lecturas`.

| Campo | Tipo BSON | Obligatorio para EPA | Regla |
|---|---|---|---|
| `_id` | `ObjectId` o identificador único elegido por MongoDB | Sí | Único **por documento**; no equivale al `sensor_id` |
| `sensor_id` | `string` | Sí | Identificador exacto en `sensor.id_sensor` |
| `zona_id` | `string` | Sí | Identificador exacto en `ubicacion.id_ubicacion` |
| `tipo_sensor` | `string` | Sí | Para EPA: `particulas` |
| `variable` | `string` | Sí | Para EPA: `pm25` o `pm10` |
| `unidad` | `string` | Sí | Unidad canónica: `µg/m³` |
| `valor` | Número BSON (`double` o `Decimal128`) | Sí | Conservar signo; elegir un tipo numérico consistente |
| `fecha_utc` | BSON `Date` | Sí | Instante UTC, **no** una cadena de texto |
| `fuente` | `string` | Sí | `EPA AQS hourly 2025` |
| `sintetico` | `bool` | Sí | `false` para EPA; `true` para datos DEMO |

El campo temporal implementado es `fecha_utc`, de tipo BSON Date. Los validadores están en `mongo/01_colecciones.js`. Se comprobó el rechazo de lecturas sin sensor_id y con fecha_utc como texto, ambas con código de validación 121.

**Ejemplo JSON extendido ilustrativo** (el valor es solo un ejemplo, no una lectura EPA verificada):

```json
{
  "sensor_id": "EPA-01-003-0010-88101-3",
  "zona_id": "EPA-01-003-0010",
  "tipo_sensor": "particulas",
  "variable": "pm25",
  "unidad": "µg/m³",
  "valor": 12.5,
  "fecha_utc": { "$date": "2025-01-01T00:00:00.000Z" },
  "fuente": "EPA AQS hourly 2025",
  "sintetico": false
}
```

En MongoDB se permiten **muchas lecturas para el mismo `sensor_id`**. Por ello, **no crear un índice único sobre `sensor_id` solamente**. El índice implementado para Q01 es `{ sensor_id: 1, fecha_utc: 1, _id: 1 }`; la política de unicidad de lecturas debe considerar además el origen, la variable y posibles revisiones de datos, y acordarse antes de imponer restricciones.

## 4. Fechas y zonas horarias

- PostgreSQL almacena `medicion.fecha_utc` como `TIMESTAMPTZ`; el ETL analiza `Date GMT` + `Time GMT` como fecha/hora **UTC**.
- MongoDB debe usar `Date` BSON del **mismo instante UTC** (visualización ISO 8601 con `Z`).
- No confundir `Date Local` / `Time Local` del CSV con UTC.
- Una medición local del 31 de diciembre de 2025 puede aparecer en UTC el **1 de enero de 2026**. En Azure se verificó el intervalo `2025-01-01 00:00:00+00` a `2026-01-01 07:00:00+00` para los registros presentes.
- `sensor.fecha_instalacion` es `NULL` cuando no hay evidencia fiable de fecha física. `First Year of Data` **no** es una fecha de instalación.
- `sensor.estado` (`activo`/`inactivo`) es una **clasificación operativa del ETL**: activo cuando `Last Sample Date >= 2025-10-01`; no representa el estado físico verificado del equipo.

## 5. Variables, unidades y precisión

| Parameter Code EPA | Variable canónica | Unidad en PostgreSQL/MongoDB | Unidad declarada en CSV |
|---|---|---|---|
| `88101` | `pm25` | `µg/m³` | `Micrograms/cubic meter (LC)` |
| `81102` | `pm10` | `µg/m³` | `Micrograms/cubic meter (25 C)` |

La expresión canónica `µg/m³` **no elimina** la diferencia en las condiciones de referencia (`LC` frente a `25 C`); el ETL **no efectúa una conversión termodinámica**. Conservar el parámetro de origen y la documentación de esas condiciones. PostgreSQL guarda valores como `NUMERIC(18,6)`; al intercambiarlos, evitar transformaciones que cambien silenciosamente la precisión.

## 6. Calidad, ausencias y procedencia

- **Negativos:** el ETL EPA los conserva sin alterarlos; no asumir que todos son concentraciones físicas válidas ni filtrarlos sin una decisión de calidad documentada.
- **Calificadores:** las filas con códigos de calificación se cargan, pero **el esquema relacional actual no guarda ese calificador**. Su trazabilidad permanece en el ZIP de origen. Una exportación desde PostgreSQL **no puede reconstruirlos** sin volver a consultar el CSV.
- **Valores faltantes:** no inventar coordenadas, contactos ni fechas. El ETL puede descartar monitores sin metadatos necesarios para satisfacer el esquema relacional; registrar estos casos en el informe de carga.
- **Nombre de estaciones:** cuando falta `Local Site Name`, el ETL utiliza un nombre identificable de respaldo; ese nombre **no debe presentarse como el nombre oficial de EPA**.
- **Organismos:** prioridad de origen `Collecting Agency` > `Reporting Agency` > `Owning Agency`. Estas funciones no son semánticamente equivalentes; `organismo_responsable.responsable` puede quedar `NULL`.
- **Proveniencia:** conservar referencia al ZIP de origen y al código de parámetro en la documentación del proceso; `medicion.fuente` solo guarda `EPA AQS hourly 2025`.

## 7. IDs internos de PostgreSQL y política de duplicados

- `medicion.id_medicion` EPA es un `BIGINT` **negativo**, derivado determinísticamente mediante BLAKE2b sobre `(sensor, parámetro, instante UTC)`; los valores positivos se reservan por convenio para `IDENTITY` y DEMO.
- **MongoDB no tiene que copiar ese `BIGINT` como `_id`**; el vínculo entre motores es por `sensor_id` y por los atributos compartidos de la observación.
- El ETL usa `ON CONFLICT` para evitar duplicados al repetir la carga. **No equivale** a verificar que un registro previamente existente tenga idéntico valor o versión.
- Para comparar observaciones entre motores, utilizar al menos `sensor_id`, `variable`, `fecha_utc` y `fuente`; valorar `POC` (ya contenido en `sensor_id`) y futuras políticas de revisiones.

## 8. Verificaciones de integración

**PostgreSQL (Azure, datos observados tras la carga masiva):**

```sql
SELECT COUNT(*) AS mediciones_epa
FROM public.medicion
WHERE fuente = 'EPA AQS hourly 2025';
-- 500000

SELECT COUNT(*) AS sensores_epa
FROM public.sensor
WHERE id_sensor LIKE 'EPA-%';
-- 1528

SELECT COUNT(*) AS mediciones_sin_sensor
FROM public.medicion m
LEFT JOIN public.sensor s ON s.id_sensor = m.id_sensor
WHERE s.id_sensor IS NULL;
-- 0
```

**Conciliación ejecutada en Ubuntu:** se utilizó
`mongo/conciliar_catalogo.py` sobre `smartcity_integracion`, con una copia
de `postgres/datos_muestra/sensor.csv` exportada de PostgreSQL.

| Indicador | Resultado |
|---|---:|
| Lecturas revisadas | 500.000 |
| Grupos sensor/zona/variable/unidad/tipo | 63 |
| Errores | 0 |

Se comprobó la correspondencia sensor/zona con el catálogo y el tipo y
unidad de las variables EPA. La prueba no consulta PostgreSQL en vivo
ni compara individualmente las mediciones entre motores.

Evidencias:
- `mongo/pruebas/evidencias/integracion/conciliacion_catalogo.txt`
- `mongo/pruebas/evidencias/integracion/catalogo_commit.txt`
- `mongo/pruebas/evidencias/integracion/catalogo_sha256.txt`

Los motores pueden tener selecciones de observaciones diferentes.

## 9. Responsabilidades y decisiones pendientes

| Responsable | Validación solicitada |
|---|---|
| Dylan — PostgreSQL | Confirmar formato de IDs, tipos PostgreSQL, catálogos, ETL y políticas de calidad |
| Fabio — SQL | Confirmar nombres y semántica útiles para consultas, fechas de instalación y rendimiento |
| Edward — MongoDB | Aprobar colección/campos, validador JSON Schema, tipo numérico y carga documental |
| Javier — MongoDB | Revisar índices, consultas, claves de búsqueda y estrategia de conciliación |

**Implementado:** colección `lecturas`, campo `fecha_utc`,
identificadores EPA compartidos y conciliación del catálogo.
Los valores EPA en MongoDB se almacenan como Decimal128.

**Decisiones pendientes:** tratamiento analítico de negativos y
calificadores, condiciones de referencia, revisiones de observaciones
e integración de la segunda fuente.

Las pruebas y sus límites están documentados en
`docs/registro_evidencia.md` y `docs/mongodb_consultas_rendimiento.md`.

## 10. Evidencias relacionadas

- `postgres/01_schema.sql`: definición de tablas, claves y restricciones.
- `postgres/02_seed.sql`: datos sintéticos de demostración.
- `postgres/carga.py`: ETL EPA AQS reproducible.
- `postgres/README_carga_epa.md`: guía de ejecución y transformaciones.
- `docs/postgres/informes/carga_azure_500k.json`: reporte de la carga en Azure (490.000 inserciones nuevas durante esa ejecución, 500.000 EPA acumuladas).
- `postgres/README.md`: descripción del modelo conceptual, lógico y normalización.

**Seguridad:** no incluir credenciales, archivos `.pgpass` ni ZIP de varios gigabytes en GitHub.
