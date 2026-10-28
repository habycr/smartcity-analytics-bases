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
## Verificación de integración en Ubuntu — Javier, 28 de octubre de 2026

Se ejecutaron los módulos de Edward desde la rama de integración.

| Comprobación | Resultado |
|---|---|
| Colecciones en smartcity_demo | Cuatro colecciones creadas con validadores |
| Validadores | Sin sensor_id y fecha_utc como texto rechazados con código 121 |
| Documento válido | Aceptado y eliminado al finalizar la prueba |
| CRUD | Inserciones, lecturas, actualizaciones y eliminación verificadas |
| Limpieza CRUD | Cero documentos DEMO-CRUD restantes |
| Generador en smartcity_integracion | Dos ejecuciones con documentos finales idénticos |
| Conteos posteriores | 500.000 lecturas, 10 eventos, 10 alertas y 3 incidentes |
| Conciliación del catálogo | 500.000 lecturas, 63 grupos, cero errores |

El catálogo utilizado es una copia de
postgres/datos_muestra/sensor.csv de feature/sprint1-postgres-modelo,
exportado previamente desde PostgreSQL. El conciliador comprobó los
pares sensor/zona y el tipo y unidad de las variables EPA.

Esta conciliación no compara las mediciones una a una ni consulta una
instancia PostgreSQL en vivo.

Se ajustó la prueba de validadores para exigir el código 121.
El generador utiliza ahora la base seleccionada en la URI de mongosh.

Las evidencias están en mongo/pruebas/evidencias/integracion/.
La revisión de consultas e índices se describe en
docs/mongodb_consultas_rendimiento.md.

### Alcance pendiente

- Ejecutar la integración en Windows.
- Verificar la recarga del ETL con los archivos originales para acreditar
  su control de duplicados; repetir el generador no prueba el ETL.
- Definir la política de calidad para valores negativos y calificadores EPA.

## Recarga del CSV de demostración

Se ejecutó mongo/carga.py dos veces con datos/mediciones_demo.csv
y datos/catalogo_demo.csv en smartcity_prueba_carga.

- Primera ejecución: 3 inserciones, 0 documentos existentes.
- Segunda ejecución: 0 inserciones, 3 documentos existentes.
- Total final: 3 lecturas sintéticas, sin filas inválidas ni sensores
  ausentes del catálogo.

Evidencias:
- mongo/pruebas/evidencias/integracion/recarga_demo_1.json
- mongo/pruebas/evidencias/integracion/recarga_demo_2.json

Esta prueba acredita el control de duplicados del CSV normalizado
de demostración. La recarga completa de los ZIP originales EPA y
la ejecución de la integración en Windows siguen pendientes.
