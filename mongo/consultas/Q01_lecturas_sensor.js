// Q01: lecturas de un sensor, ordenadas por fecha.
// Cambiar este valor para consultar otro sensor.
const sensorId = "S001";

const base = db.getSiblingDB("smartcity");

const resultados = base.lecturas.find(
  { sensor_id: sensorId },
  {
    _id: 0,
    sensor_id: 1,
    zona_id: 1,
    variable: 1,
    valor: 1,
    unidad: 1,
    fecha: 1
  }
).sort({ fecha: 1, _id: 1 }).toArray();

print(`Lecturas del sensor ${sensorId}: ${resultados.length}`);
printjson(resultados);
