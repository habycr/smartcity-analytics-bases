# Guia de ejecucion MongoDB: Ubuntu y Windows

## Requisitos comunes

- MongoDB Community Server 8.0 instalado.
- mongosh instalado y disponible en la terminal.
- Archivos del proyecto guardados en UTF-8.
- Ejecutar los comandos desde la raiz de smartcity-analytics.

MongoDB Compass es opcional y no sustituye al servidor.
Cada integrante utiliza su propia base local.
No es necesario compartir las carpetas internas de MongoDB:
los datos se reproducen mediante los scripts de carga.

# Ubuntu

## 1. Entrar al proyecto

cd ~/Documentos/smartcity-analytics

## 2. Iniciar y verificar MongoDB

sudo systemctl start mongod
systemctl is-active mongod

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --eval 'db.runCommand({ ping: 1 })'

Esperado: active y { ok: 1 }.

## 3. Cargar la muestra

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/carga/muestra.js

## 4. Crear indices

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/indices/crear_indices.js

## 5. Ejecutar una consulta

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/consultas/Q01_lecturas_sensor.js

## 6. Ejecutar las diez consultas

(
  set -e
  for archivo in mongo/consultas/Q*.js; do
    echo "Ejecutando: $archivo"
    mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file "$archivo"
  done
)

## 7. Ejecutar las pruebas

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/pruebas/verificar_muestra.js

bash mongo/pruebas/verificar_agregaciones.sh

Esperado:
- 11 comprobaciones basicas aprobadas.
- Cinco consultas de agregacion aprobadas.

## 8. Guardar comparacion de planes

mkdir -p mongo/pruebas/evidencias

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/indices/comparar_planes.js > mongo/pruebas/evidencias/comparacion_planes_muestra.txt

## 9. Ejecutar benchmark independiente

mongosh "mongodb://127.0.0.1:27017/smartcity_rendimiento" --quiet --file mongo/pruebas/rendimiento.js > mongo/pruebas/evidencias/rendimiento_500k.txt

cat mongo/pruebas/evidencias/rendimiento_500k.txt

# Windows: PowerShell

## 1. Entrar al proyecto

Adaptar la ruta a la ubicacion real:

cd "C:\Users\Edward\Documents\smartcity-analytics"

## 2. Comprobar mongosh

mongosh --version

Si no se reconoce, instalar mongosh o agregar su carpeta al PATH.
Despues de modificar el PATH, abrir una nueva terminal.

## 3. Iniciar y verificar MongoDB

Si MongoDB fue instalado como servicio con el nombre predeterminado,
abrir PowerShell como administrador y ejecutar:

Get-Service -Name MongoDB
Start-Service -Name MongoDB

Una vez iniciado el servicio, los comandos restantes pueden
ejecutarse desde PowerShell normal.

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --eval 'db.runCommand({ ping: 1 })'

Esperado: { ok: 1 }.

Si Get-Service indica que el servicio no existe, revisar la instalacion
de MongoDB Server y el nombre del servicio configurado.

## 4. Cargar la muestra

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/carga/muestra.js

## 5. Crear indices

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/indices/crear_indices.js

## 6. Ejecutar una consulta

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/consultas/Q01_lecturas_sensor.js

## 7. Ejecutar las diez consultas

Get-ChildItem "mongo/consultas/Q*.js" | Sort-Object Name | ForEach-Object {
    Write-Host "Ejecutando: $($_.Name)"
    mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file $_.FullName
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo la consulta $($_.Name)"
    }
}

## 8. Ejecutar las pruebas basicas

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/pruebas/verificar_muestra.js

Esperado: 11 comprobaciones aprobadas.

La prueba verificar_agregaciones.sh requiere Bash.
Si se tiene Git Bash instalado, abrir Git Bash en la raiz del
proyecto y ejecutar:

bash mongo/pruebas/verificar_agregaciones.sh

Esta prueba utiliza el MongoDB local de Windows.
No necesita instalar otro servidor en WSL.

## 9. Guardar comparacion de planes

New-Item -ItemType Directory -Force -Path "mongo/pruebas/evidencias" | Out-Null

mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --file mongo/indices/comparar_planes.js | Out-File -Encoding utf8 "mongo/pruebas/evidencias/comparacion_planes_muestra.txt"

## 10. Ejecutar benchmark independiente

mongosh "mongodb://127.0.0.1:27017/smartcity_rendimiento" --quiet --file mongo/pruebas/rendimiento.js | Out-File -Encoding utf8 "mongo/pruebas/evidencias/rendimiento_500k.txt"

Get-Content "mongo/pruebas/evidencias/rendimiento_500k.txt"

# Consideraciones para ambos sistemas

- La muestra contiene 8 lecturas, 3 eventos, 2 alertas y 3 incidentes.
- Repetir muestra.js restablece sus documentos sin duplicarlos.
- No elimina otros documentos presentes en las colecciones.
- Las pruebas de agregaciones esperan una base con solo la muestra.
- Ejecutar estas pruebas antes de incorporar la carga definitiva.
- El benchmark genera 500.000 documentos sinteticos en una base aparte.
- No reemplaza la carga final del proyecto.
- Los tiempos de rendimiento pueden variar entre computadoras.
- Los scripts fijan internamente sus bases mediante getSiblingDB.
  Cambiar solo el nombre de la base en la URI no cambia ese destino.
- Mantener los campos y tipos de docs/contrato_mongo.md.
- Conservar evidencia de cada equipo por separado si se desea comparar:
  los comandos de redireccion sobrescriben el archivo de salida.
