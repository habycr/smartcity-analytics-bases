# MongoDB: consultas, agregaciones e indices

## Alcance

Implementacion de las diez consultas obligatorias MongoDB del sprint 1.
Incluye datos sinteticos de desarrollo, indices, verificaciones y un
experimento de rendimiento independiente.

## Consultas

Los archivos estan en mongo/consultas/.
Los parametros se modifican al inicio del archivo correspondiente.

| Archivo | Resultado |
|---|---|
| Q01_lecturas_sensor.js | Lecturas de un sensor, ordenadas por fecha |
| Q02_lecturas_fechas.js | Lecturas dentro de un intervalo temporal |
| Q03_maximos_minimos.js | Minimos y maximos por variable y unidad |
| Q04_eventos_criticos.js | Eventos con severidad critica |
| Q05_alertas_zona.js | Cantidad de alertas por zona |
| Q06_promedios_zona.js | Promedios por zona, variable y unidad |
| Q07_promedios_tipo_sensor.js | Promedios por tipo, variable y unidad |
| Q08_incidentes_categoria.js | Cantidad de incidentes por categoria |
| Q09_evolucion_diaria.js | Promedio diario por zona para una variable |
| Q10_filtros_multiples.js | Lecturas filtradas por zona, tipo, variable, unidad, fechas y valor |

## Decisiones

- Se usan fechas BSON Date y agrupacion diaria en UTC.
- Los intervalos incluyen el inicio y excluyen el final.
- Se separan variables y unidades antes de calcular estadisticas.
- Los promedios ponderan cada lectura por igual.
- Q04 recupera eventos ya clasificados; no genera eventos.
- Q05 y Q08 muestran grupos con documentos registrados.
- Q09 no completa dias sin lecturas ni interpola valores.
- Los umbrales de la muestra son ficticios y no normativos.
- Las consultas actuales cargan su resultado en memoria con toArray.
  Para resultados extensos debe incorporarse paginacion o iteracion
  por cursor en la integracion con la interfaz.

## Indices iniciales

Definidos en mongo/indices/crear_indices.js.

| Indice | Uso previsto |
|---|---|
| idx_lecturas_sensor_fecha | Q01: sensor y orden temporal |
| idx_lecturas_fecha | Q02: rango temporal |
| idx_lecturas_variable_unidad_fecha | Q09: variable, unidad y fechas |
| idx_lecturas_filtros_fecha | Q10: igualdades y rango temporal |
| idx_eventos_severidad_fecha | Q04: severidad y orden temporal |

La utilidad de estos indices depende del volumen, distribucion,
selectividad y consultas. No se afirma que todos esten optimizados.
Las agrupaciones sobre toda una coleccion pueden requerir recorrerla.
Los indices tambien consumen almacenamiento y encarecen escrituras.

## Verificacion historica con la muestra

Las diez consultas fueron ejecutadas y sus resultados revisados
sobre una muestra de 8 lecturas, 3 eventos, 2 alertas y 3 incidentes.

mongo/pruebas/verificar_muestra.js:
11 comprobaciones aprobadas, incluyendo conteos, extremos,
filtros y casos sin resultados.

mongo/pruebas/verificar_agregaciones.sh:
ejecuta los archivos reales Q05-Q09 y compara sus resultados
con valores esperados. Las cinco consultas aprobaron.

Las comprobaciones basicas de Q01-Q04 y Q10 no ejecutan sus archivos
reales; verifican datos y operaciones equivalentes.
No se presenta esta verificacion como cobertura automatica completa.

Las pruebas de agregaciones requieren la base con solo la muestra.
Antes de agregar datos finales se debe aislar el entorno de pruebas.

## Experimento con 500.000 documentos

Script: mongo/pruebas/rendimiento.js
Evidencia: mongo/pruebas/evidencias/rendimiento_500k.txt

- MongoDB: 8.0.34.
- Sistema utilizado: Ubuntu 24.04, kernel 6.8.0-147-generic.
- Base independiente: smartcity_rendimiento.
- Coleccion: lecturas_benchmark_v1.
- Datos: 500.000 lecturas sinteticas.
- Sensores: 1.000, con 500 lecturas por sensor.
- Filtro: sensor_id igual a S0001.
- Orden: fecha e identificador ascendentes.
- Indice: sensor_id, fecha, _id.
- Una ejecucion de calentamiento por estrategia.
- Cinco mediciones por estrategia, alternando el orden.
- Se comprobo igualdad de los 500 identificadores devueltos.

| Metrica | Recorrido completo | Con indice |
|---|---:|---:|
| Resultados | 500 | 500 |
| Documentos examinados | 500000 | 500 |
| Claves examinadas | 0 | 500 |
| Tiempos en ms | 196, 202, 208, 208, 215 | 1, 1, 1, 2, 1 |
| Mediana en ms | 208 | 1 |

El acceso por indice examino 1.000 veces menos documentos.
La relacion entre medianas fue 208 a 1 en este experimento.

## Limites de la medicion

- Se usaron datos sinteticos uniformes y ejecucion local.
- hint fuerza las estrategias: no demuestra la eleccion automatica
  del optimizador.
- Se mide el tiempo reportado por explain, no la latencia completa
  de una aplicacion con transferencia de resultados.
- Hay calentamiento; no es una prueba con cache fria.
- Los tiempos pequenos tienen resolucion limitada.
- No se midieron escrituras, concurrencia ni costo de almacenamiento.
- El experimento valida el patron de acceso de Q01.
  No acredita el rendimiento de las otras nueve consultas.
- Los 500.000 documentos del benchmark no reemplazan la carga final
  de las fuentes del proyecto.

## Integración con la carga de Edward

Las consultas Q01-Q10 y los scripts de índices usan `fecha_utc` y la
base seleccionada en la URI. Se ejecutaron sobre `smartcity_integracion`.

| Comprobación | Resultado observado |
|---|---|
| Restauración | 500.023 documentos, cero fallos |
| Q01 | 8.466 lecturas del sensor EPA-01-003-0010-88101-3 |
| Q02 | 987 lecturas en [2025-01-01, 2025-01-02), UTC |
| Q03 | 250.000 lecturas por variable; extremos contrastados |
| Q04 | 10 eventos críticos de demostración |
| Q05 | 10 alertas en 7 zonas |
| Q06 | Los grupos suman 500.000 lecturas; un promedio contrastado |
| Q07 | Promedios: pm25 = 7,532848; pm10 = 23,409944 |
| Q08 | Ambiental: 2; infraestructura: 1 |
| Q09 | Días y variable comprobados; un grupo contrastado |
| Q10 | 222 identificadores, filtros y orden comprobados |

Q03: pm25 tiene mínimo -10 y máximo 931,3; pm10 tiene mínimo -46
y máximo 5.133,3. Se conservaron los valores negativos.

### Acceso de Q01 sobre EPA

| Métrica | Recorrido completo | Índice |
|---|---:|---:|
| Resultados | 8466 | 8466 |
| Documentos examinados | 500000 | 8466 |
| Claves examinadas | 0 | 8466 |
| Tiempo observado en ms | 167 | 7 |

Se comprobó igualdad de identificadores y orden entre ambas estrategias.
Sin hint, MongoDB también eligió idx_lecturas_sensor_fecha mediante
IXSCAN y FETCH, sin una etapa SORT adicional.

Estos tiempos corresponden a una ejecución por estrategia; no son medianas.
El benchmark sintético anterior conserva sus resultados independientes.

### Fechas, evidencia y alcance

Se comprobaron 499.602 lecturas en 2025 UTC y 398 en enero de 2026 UTC,
inicio incluido, final excluido e intervalo sin resultados.
Estos controles temporales usan operaciones equivalentes; no ejecutan
Q02 con parámetros alternativos.

Las salidas guardadas están en mongo/pruebas/evidencias/integracion/.
Parte de las comprobaciones se ejecutó desde terminal; todavía no hay
una suite automatizada completa de integración.

Las pruebas históricas de la muestra requieren adaptación al nuevo esquema.
La revisión de validadores, CRUD, referencias con PostgreSQL y calidad
de datos queda fuera de esta validación de consultas.
