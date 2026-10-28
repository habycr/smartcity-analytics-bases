// Q01: lecturas de un sensor, ordenadas por fecha_utc.
// Cambiar este valor para consultar otro sensor.
const sensorId = "EPA-01-003-0010-88101-3";

const base = db;

const resultados = base.lecturas.find(
  { sensor_id: sensorId },
  {
    _id: 0,
    sensor_id: 1,
    zona_id: 1,
    variable: 1,
    valor: 1,
    unidad: 1,
    fecha_utc: 1
  }
).sort({ fecha_utc: 1, _id: 1 }).toArray();

print(`Lecturas del sensor ${sensorId}: ${resultados.length}`);
printjson(resultados);
