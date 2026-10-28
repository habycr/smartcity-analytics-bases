# Ejecución MongoDB: Ubuntu y Windows

## Requisitos

- MongoDB Server y mongosh.
- MongoDB Database Tools para utilizar mongorestore.
- Ejecutar los comandos desde la raíz del repositorio.
- Cada integrante utiliza su propio servidor local.

Guardar smartcity_500k.archive.gz en mongo/backups/, sin descomprimir.
El respaldo debe permanecer excluido de Git.

## Iniciar el servidor

Ubuntu:

```bash
sudo systemctl start mongod
```

En el equipo Ubuntu utilizado, MongoDB funcionó con el kernel
6.8.0-147-generic. El arranque con 7.0.0-38-generic fue rechazado
por la versión instalada de MongoDB.

Windows, PowerShell como administrador si el servicio se llama MongoDB:

```powershell
Get-Service -Name MongoDB
Start-Service -Name MongoDB
```

Los comandos restantes pueden ejecutarse desde una terminal normal.

## Comprobar conexión y destino

Los siguientes comandos funcionan en Bash y PowerShell:

```text
mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --eval 'db.runCommand({ ping: 1 })'
mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --eval 'printjson(db.getCollectionNames())'
```

## Restauración inicial

Ejecutar únicamente en una base de destino vacía.
Si ya se restauró correctamente, continuar con los índices.

```text
mongorestore --uri="mongodb://127.0.0.1:27017" --gzip --archive="mongo/backups/smartcity_500k.archive.gz" --nsFrom="smartcity.*" --nsTo="smartcity_integracion.*"
```

Esperado: 500.000 lecturas, 10 eventos, 10 alertas y 3 incidentes.
No cargar muestra.js en esta base.

## Índices y consulta individual

Comandos comunes para ambos sistemas:

```text
mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --file mongo/indices/crear_indices.js
mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --file mongo/consultas/Q01_lecturas_sensor.js
mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --file mongo/indices/comparar_planes.js
```

Q01-Q10 y los scripts de índices usan la base indicada en la URI.
El campo temporal es fecha_utc.
Los parámetros se ajustan al inicio de cada consulta.

## Ejecutar todas las consultas

Ubuntu, Bash:

```bash
(
  set -e
  for archivo in mongo/consultas/Q*.js; do
    mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --file "$archivo"
  done
)
```

Windows, PowerShell:

```powershell
Get-ChildItem "mongo/consultas/Q*.js" | Sort-Object Name | ForEach-Object {
    mongosh "mongodb://127.0.0.1:27017/smartcity_integracion" --quiet --file $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Falló la consulta $($_.Name)"
    }
}
```

## Evidencias y pruebas anteriores

Consultar docs/mongodb_consultas_rendimiento.md para resultados y límites.
Las evidencias guardadas están en mongo/pruebas/evidencias/integracion/.

verificar_muestra.js y verificar_agregaciones.sh pertenecen a la muestra
histórica con fecha y parámetros antiguos. Requieren adaptación antes de
utilizarlos para evaluar las consultas actuales.
El archivo .sh necesita Bash, incluido Git Bash en Windows.

El benchmark rendimiento.js conserva su base interna smartcity_rendimiento
y su esquema independiente. Sus resultados no equivalen a los de EPA.

Los comandos están preparados para Bash y PowerShell.
La ejecución de esta integración se verificó en Ubuntu.
Falta comprobarla en Windows.
