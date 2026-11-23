# Ejecución del módulo MongoDB — Sprint 1

Ejecutar desde la raíz del repositorio. Requiere MongoDB 8.0 en funcionamiento, `mongosh`, Python 3.13 y las dependencias indicadas en `requirements.txt`.

## Preparación

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
mongosh "mongodb://127.0.0.1:27017" --file mongo/01_colecciones.js
mongosh "mongodb://127.0.0.1:27017" --file mongo/02_muestra.js
mongosh "mongodb://127.0.0.1:27017" --file mongo/pruebas/validadores.js
mongosh "mongodb://127.0.0.1:27017" --file mongo/03_crud.js
```

Los comandos anteriores utilizan `smartcity_demo`. El archivo `02_muestra.js` contiene datos sintéticos; no debe ejecutarse sobre `smartcity`.

## Carga EPA AQS 2025

Los archivos originales se ubican localmente en `datos/reales/` y no se suben a Git. Se requiere un CSV `datos/reales/catalogo_postgres.csv` con encabezados `id_sensor,id_ubicacion`, obtenido del catálogo compartido de PostgreSQL.

```powershell
$env:SMARTCITY_DB="smartcity"
mongosh "mongodb://127.0.0.1:27017" --file mongo/01_colecciones.js
Remove-Item Env:SMARTCITY_DB
.\.venv\Scripts\python.exe mongo/carga.py --archivo datos/reales/hourly_88101_2025.zip --catalogo datos/reales/catalogo_postgres.csv --bd smartcity --limite-reales 250000 --lote 1000 --reporte docs/reporte_epa_pm25_250k.json
.\.venv\Scripts\python.exe mongo/carga.py --archivo datos/reales/hourly_81102_2025.zip --catalogo datos/reales/catalogo_postgres.csv --bd smartcity --limite-reales 250000 --lote 1000 --reporte docs/reporte_epa_pm10_250k.json
.\.venv\Scripts\python.exe mongo/conciliar_catalogo.py --catalogo datos/reales/catalogo_postgres.csv --bd smartcity
mongosh "mongodb://127.0.0.1:27017" --file mongo/04_generar_demostraciones.js
$env:SMARTCITY_DB="smartcity"
mongosh "mongodb://127.0.0.1:27017" --file mongo/pruebas/conteos.js
Remove-Item Env:SMARTCITY_DB
```

**Nota de reproducibilidad:** las dos cargas separadas de 250.000 lecturas permiten obtener 250.000 PM2.5 y 250.000 PM10. El cargador utiliza identificadores determinísticos y no duplica observaciones ya cargadas. Los reportes JSON pueden mostrar menos inserciones nuevas si ya se ejecutó el proceso previamente.

## Verificación

Para consultar el resultado en Compass, conectarse a `mongodb://127.0.0.1:27017`, abrir la base **`smartcity`** y la colección **`lecturas`**. `smartcity_demo` contiene únicamente datos de prueba.

Las consultas Q01–Q10 e índices se ejecutan desde el módulo de consultas MongoDB del grupo una vez integrado con `fecha_utc`.
