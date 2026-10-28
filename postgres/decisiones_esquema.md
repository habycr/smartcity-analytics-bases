# Decisiones de implementación — PostgreSQL / EPA AQS

**Estado:** `01_schema.sql` versión inicial. No se han cargado datos ni probado aún en Azure.

## Esquema aprobado

Se conservan **8 tablas**, **8 PK** y **6 FK** del modelo lógico; `usuario` es independiente. Identificadores interoperables `sensor.id_sensor` y `ubicacion.id_ubicacion`: `VARCHAR(64)`, con la misma representación textual que `sensor_id` y `zona_id` en MongoDB.

## Reglas acordadas

- `sensor.estado`: solo `activo` e `inactivo` (`CHECK`), sin atribuir necesariamente condición física real.
- `categoria_sensor.nombre_categoria`, `variable_medicion.nombre_variable` y `usuario.correo` son `UNIQUE` y `NOT NULL`.
- `usuario.correo` se conserva tal como lo ingresa el usuario; la unicidad de `VARCHAR` normalmente distingue mayúsculas/minúsculas.
- `usuario.apellido2` admite `NULL`.
- `organismo_responsable.nombre` **no** tiene `UNIQUE` por ahora.
- Las seis FK siguen siendo `NOT NULL` y usan `ON DELETE RESTRICT`.
- Coordenadas `NUMERIC(9,6)` dentro de los rangos geográficos.
- `medicion.fecha_utc` es `TIMESTAMPTZ`; en la carga EPA se interpretan las columnas GMT como UTC.

## Ajustes justificados por la auditoría EPA

- `sensor.fecha_instalacion` admite `NULL`: `First Year of Data` no certifica la fecha física de instalación.
- `organismo_responsable.responsable` admite `NULL`: significado pendiente y los datos no proveen un contacto fiable universal.
- `ubicacion.nombre_zona` sigue siendo obligatorio. Durante la carga debe derivarse un nombre descriptivo con el ID oficial si `Local Site Name` está vacío; se documentará como generado.
- `ubicacion.distrito` se llena con `County Name` como equivalente administrativo **aproximado**, indicado en documentación.
- Los monitores de EPA no equivalen necesariamente uno a uno a equipos físicos independientes.
- Monitores sin `Collecting Agency` / `Reporting Agency`: resolver con procedimiento explícito (incluyendo `Owning Agency` si está disponible), registrando el rol real. No inventar responsables ni asignar un organismo ficticio como si fuese oficial.
- En los CSV horarios existen **12.316.717** mediciones, **223.852** valores negativos, códigos `Qualifier` y diferencias `LC` / `25 C`. Los valores negativos no se prohíben con `CHECK` hasta fijar una política de calidad sustentada.
- No se impone `UNIQUE(sensor, variable, fecha)` todavía: la auditoría no encontró duplicados en los dos archivos inspeccionados, pero habrá otras fuentes y potenciales reprocesamientos. El ETL debe definir una clave de idempotencia.
- Códigos `Method Code`, `Qualifier`, `MDL` y unidades originales se conservan en origen/etapa ETL; no forman parte de las ocho tablas actuales.

## Tareas previas a carga masiva

1. Seleccionar los monitores de los dos parámetros de 2025 y resolver el organismo con trazabilidad.
2. Establecer fecha fija de referencia y regla reproducible para el estado de actividad.
3. Determinar política EPA para valores negativos, calificadores y condiciones de unidad.
4. Publicar catálogo de IDs para MongoDB; usar los mismos prefijos y ceros iniciales.
5. Probar el SQL en una base vacía local; solo después ejecutar en Azure.
6. Coordinar con Fabio cualquier índice adicional, evitando duplicar su trabajo.
