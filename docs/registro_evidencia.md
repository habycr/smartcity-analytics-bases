# Registro de pruebas — MongoDB

**Proyecto:** SmartCity Analytics
**Responsable:** Edward
**Sprint:** 1

## Pruebas realizadas

| Prueba | Resultado |
|---|---|
| Creación de colecciones | 4 colecciones creadas correctamente |
| Validadores JSON Schema | Documentos inválidos rechazados correctamente |
| Operaciones CRUD | 7 operaciones ejecutadas exitosamente |
| Conexión Python–MongoDB | Conexión establecida mediante PyMongo |
| Carga de datos | 500.000 lecturas reales EPA |
| Control de duplicados | Sin duplicaciones en las pruebas de recarga |
| Validación de identificadores | 500.000 documentos revisados, 0 errores |
| Eventos | 10 documentos simulados |
| Alertas | 10 documentos simulados |
| Incidentes | 3 documentos simulados |

## Resultados

Se implementó una base documental MongoDB para almacenar mediciones de calidad del aire correspondientes a PM2.5 y PM10.

Se cargaron 500.000 documentos reales provenientes de EPA AQS 2025 mediante Python y PyMongo.

Las pruebas realizadas permitieron comprobar el funcionamiento de las colecciones, los validadores, las operaciones CRUD y el proceso de carga.

La verificación de identificadores contra el catálogo compartido de PostgreSQL no detectó inconsistencias.

Los eventos, alertas e incidentes incorporados son simulaciones utilizadas para demostrar el funcionamiento del modelo documental.

## Alcance de estas pruebas

Este registro corresponde al módulo de modelo e ingestión MongoDB. La ejecución de las diez consultas analíticas y la evaluación de índices pertenecen al módulo de consultas del equipo. Los cuatro archivos originales utilizados para mediciones provienen de una sola fuente, EPA AQS.