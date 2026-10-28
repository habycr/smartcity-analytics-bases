# Generación de eventos, alertas e incidentes demostrativos — Sprint 1

**Responsable:** Edward, módulo MongoDB (modelo y carga).

## Propósito y alcance

En `smartcity`, la colección `lecturas` contiene 500.000 registros de PM2.5 y PM10 provenientes de EPA AQS hourly 2025, cargados desde `hourly_88101_2025.zip` y `hourly_81102_2025.zip`. Las colecciones `eventos`, `alertas` e `incidentes` se utilizaron para **demostrar las estructuras documentales y las consultas** del Sprint 1. EPA AQS no suministra en esos archivos incidentes municipales ni alertas emitidas por una autoridad.

## Reglas de demostración

El script `mongo/04_generar_demostraciones.js` busca un máximo de cinco lecturas observadas por variable con valores superiores a estos umbrales **ilustrativos y no normativos**:

| Variable | Umbral de simulación | Unidad |
|---|---:|---|
| PM2.5 (`pm25`) | 40 | µg/m³ |
| PM10 (`pm10`) | 80 | µg/m³ |

Por cada lectura seleccionada, se inserta/actualiza un `evento` con `severidad: 'critica'` y una `alerta` con `estado: 'pendiente'`. Esta clasificación **solo aplica en la simulación académica** y no representa una determinación oficial de riesgo, ni la existencia de una alerta real. Los incidentes son tres **escenarios completamente ficticios** ubicados en zonas existentes del catálogo de lecturas; no se debe interpretar que ocurrieron allí.

Todos estos documentos se distinguen de las lecturas de origen con `sintetico: true`, `fuente: 'DEMO - reglas ilustrativas sobre EPA AQS 2025'` y `detalle` explicativo. Los eventos/alertas incluyen referencia al identificador de la lectura EPA de origen (`lectura_id`) y las alertas al evento (`evento_id`). Los identificadores de sensor y ubicación provienen de lecturas existentes.

## Reproducibilidad

Desde la raíz del repositorio, con MongoDB local levantado:

```powershell
mongosh "mongodb://127.0.0.1:27017" --file mongo/04_generar_demostraciones.js
```

Las operaciones son `replaceOne` con `upsert: true` e `_id` determinísticos, por lo que repetir el script actualiza los mismos documentos de prueba en vez de añadir duplicados. No borra ni modifica las 500.000 lecturas reales.

**Alcance:** los umbrales son reglas de demostración académica. Ninguna alerta ni incidente simulado representa una notificación oficial de EPA o de una municipalidad.
