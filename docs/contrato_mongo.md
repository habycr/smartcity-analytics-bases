# Contrato de datos MongoDB

## Alcance y responsables

Este documento define la estructura inicial que deben conservar las cargas
para funcionar con las consultas Q01-Q10 del sprint 1.

Javier implementó consultas, agregaciones, índices y pruebas.
Edward incorporó el modelo documental, validadores, fuentes, carga masiva,
operaciones CRUD y generación de eventos y alertas de demostración.
La validación de consultas no acredita por sí sola todos estos módulos.
Los cambios de nombres, tipos o significado de campos deben coordinarse
antes de modificar la carga o las consultas.

El contrato documenta la estructura; no instala validadores ni comprueba
referencias automáticamente. Se permiten campos adicionales.

## Conexión y compatibilidad

- URI local: `mongodb://127.0.0.1:27017`.
- Base de integración: `smartcity_integracion`.
- Colecciones: `lecturas`, `eventos`, `alertas`, `incidentes`.
- MongoDB Community Server 8.0 y `mongosh`, en Ubuntu o Windows.
- Archivos de scripts y documentación en UTF-8.

Cada integrante utiliza su propio servidor local. La muestra se reproduce
con `mongo/carga/muestra.js`; no se comparten carpetas internas del servidor.
La prueba `verificar_agregaciones.sh` necesita Bash, incluido Git Bash
en Windows. Consultar [la guía de ejecución](guia_ejecucion_mongodb.md).

Q01-Q10 y los scripts de mongo/indices/ utilizan la base seleccionada
en la URI de mongosh mediante `db`. Indicar siempre la base al ejecutarlos.
Los scripts históricos de muestra, pruebas y benchmark pueden fijar
sus propias bases internamente.

## Reglas comunes

- `sensor_id` y `zona_id`: cadenas estables, coordinadas con el catálogo PostgreSQL.
- `_id`: único dentro de cada colección. La muestra usa cadenas.
  La carga final puede usar otro tipo BSON válido, conservando exactamente
  el valor y tipo del identificador en sus referencias.
- `fecha_utc`: BSON Date con instantes expresados en UTC; no guardar texto
  como sustituto de este campo.
- Rangos de consulta: inicio incluido y final excluido (`$gte`, `$lt`).
- Agrupación diaria: UTC.
- `valor` y `umbral`: números BSON, nunca cadenas ni valores nulos.
- Mantener consistencia entre `tipo_sensor`, `variable` y `unidad`.
  Convertir unidades antes de combinar observaciones que deban compararse.
- `fuente`: cadena que identifica la procedencia.
- `sintetico`: booleano que distingue datos generados de observaciones reales.
- Los campos listados deben estar presentes salvo los marcados como opcionales.
- La carga debe comprobar las referencias: MongoDB no las valida como claves foráneas.

## lecturas

| Campo | Tipo | Uso |
|---|---|---|
| `_id` | Identificador BSON | Identifica la lectura |
| `sensor_id` | Cadena | Sensor del catálogo |
| `zona_id` | Cadena | Zona del catálogo |
| `tipo_sensor` | Cadena | Clasificación del sensor |
| `variable` | Cadena | Magnitud medida |
| `valor` | Número | Valor observado o generado |
| `unidad` | Cadena | Unidad de la magnitud |
| `fecha_utc` | BSON Date | Instante de la lectura |
| `fuente` | Cadena | Procedencia |
| `sintetico` | Booleano | Indica si es un dato generado |

La muestra utiliza `termometro / temperatura / °C` y
`particulas / pm25 / µg/m³`. Estos valores no limitan las fuentes futuras;
los filtros de las consultas deben ajustarse a los valores acordados.
No cambiar la escritura de las unidades entre documentos equivalentes.

## eventos

| Campo | Tipo | Uso |
|---|---|---|
| `_id` | Identificador BSON | Identifica el evento |
| `sensor_id` | Cadena | Sensor asociado |
| `zona_id` | Cadena | Zona asociada |
| `lectura_id` | Mismo tipo que `lecturas._id` | Referencia opcional a la lectura |
| `categoria` | Cadena | Categoría del evento |
| `severidad` | Cadena | Q04 busca exactamente `"critica"` |
| `fecha_utc` | BSON Date | Instante del evento |
| `fuente` | Cadena | Procedencia |
| `sintetico` | Booleano | Indica si es un dato generado |

Q04 recupera eventos ya clasificados; no los genera.

## alertas

| Campo | Tipo | Uso |
|---|---|---|
| `_id` | Identificador BSON | Identifica la alerta |
| `evento_id` | Mismo tipo que `eventos._id` | Referencia opcional al evento asociado |
| `sensor_id` | Cadena | Sensor asociado |
| `zona_id` | Cadena | Zona asociada; agrupación de Q05 |
| `variable` | Cadena | Magnitud que originó la alerta |
| `valor` | Número | Valor asociado |
| `umbral` | Número | Umbral aplicado |
| `unidad` | Cadena | Unidad común de valor y umbral |
| `estado` | Cadena | Estado de atención |
| `fecha_utc` | BSON Date | Instante de la alerta |
| `fuente` | Cadena | Procedencia |
| `sintetico` | Booleano | Indica si es un dato generado |

La muestra usa estado `pendiente` y umbral 40 para pm25.
Ese umbral es ficticio y no normativo. El módulo integrado incluye
`mongo/04_generar_demostraciones.js` para generar eventos, alertas e
incidentes de demostración.

## incidentes

| Campo | Tipo | Uso |
|---|---|---|
| `_id` | Identificador BSON | Identifica el incidente |
| `zona_id` | Cadena | Zona asociada |
| `categoria` | Cadena | Agrupación de Q08 |
| `descripcion` | Cadena | Descripción del incidente |
| `fecha_utc` | BSON Date | Instante del incidente |
| `fuente` | Cadena | Procedencia |
| `sintetico` | Booleano | Indica si es un dato generado |

## Muestra y separación de entornos

`mongo/carga/muestra.js` carga 8 lecturas, 3 eventos, 2 alertas y 3 incidentes.
Usa `replaceOne` con `upsert` por `_id`: repetirlo restablece los documentos
de la muestra sin duplicarlos ni eliminar documentos ajenos.

Se reservan los identificadores L001-L008, E001-E003, A001-A002 e I001-I003.
La carga definitiva debe evitar colisiones con ellos.

Las consultas actuales incluyen todos los documentos que cumplen sus filtros,
incluidos los sintéticos. Antes de analizar datos reales se debe acordar
si la muestra se conserva en una base separada o se incorpora un filtro.

Las pruebas de agregaciones esperan una base con solo la muestra.
Ejecutarlas antes de la carga definitiva; para mantenerlas después,
primero adaptar los scripts para seleccionar una base de pruebas aislada.

El benchmark utiliza `smartcity_rendimiento.lecturas_benchmark_v1`.
Sus 500.000 documentos sintéticos no sustituyen la carga de fuentes del proyecto.

## Consultas que dependen del contrato

| Consulta | Resultado |
|---|---|
| Q01 | Lecturas por sensor, ordenadas por fecha |
| Q02 | Lecturas por rango temporal |
| Q03 | Máximos y mínimos por variable y unidad |
| Q04 | Eventos con severidad `critica` |
| Q05 | Cantidad de alertas por zona |
| Q06 | Promedio por zona, variable y unidad |
| Q07 | Promedio por tipo de sensor, variable y unidad |
| Q08 | Cantidad de incidentes por categoría |
| Q09 | Evolución diaria por zona, variable y unidad |
| Q10 | Filtros por zona, tipo, variable, unidad, fechas y valor |

Los promedios ponderan cada lectura por igual. Q09 no completa días sin datos.
Los parámetros de sensor, fechas y categorías de ejemplo deben ajustarse
para consultar la carga definitiva.

## Comprobaciones de integración

Los módulos de modelo, validadores, carga, CRUD y generación de datos
de demostración de Edward están incluidos en la rama de integración.
Para evaluar el conjunto corresponde comprobar:

1. Correspondencia del modelo y validadores con este contrato.
2. Procedencia de las fuentes y distinción de datos reales y simulados.
3. Reproducibilidad de la carga y control de duplicados.
4. Operaciones CRUD y generación de eventos, alertas e incidentes.
5. Tipos, unidades y referencias compartidas con PostgreSQL.
6. Resultados de Q01-Q10 y planes de acceso con los datos integrados.

Se ejecutaron Q01-Q10 sobre el respaldo de Edward restaurado en
`smartcity_integracion`: 500.000 lecturas, 10 eventos, 10 alertas y
3 incidentes. Se comprobaron los resultados principales y el acceso
indexado de Q01. Esta validación no acredita los validadores, el CRUD,
la generación de eventos ni la integración con PostgreSQL.
Consultar [consultas y rendimiento](mongodb_consultas_rendimiento.md).



## Compatibilidad con la muestra anterior

El campo temporal del modelo integrado es `fecha_utc`.
La muestra histórica utiliza `fecha` y parámetros diferentes.
Sus pruebas requieren adaptación antes de evaluar las consultas actuales.

No ejecutar `mongo/carga/muestra.js` sobre `smartcity_integracion`.
El benchmark sintético conserva su esquema independiente.

La carga EPA utiliza Decimal128 para `valor`, variables `pm25` y `pm10`,
tipo `particulas` y unidad `µg/m³`.
Los valores negativos se conservaron; su tratamiento de calidad sigue
pendiente de una decisión documentada.
Los eventos y alertas revisados son datos de demostración.
