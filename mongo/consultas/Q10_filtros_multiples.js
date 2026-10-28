// Q10: combinar zona, tipo, variable, unidad, fechas y valor.
// El umbral es ficticio para desarrollo; no es un limite normativo.
const zonaId = "EPA-04-013-0019";
const tipoSensor = "particulas";
const variable = "pm25";
const unidad = "µg/m³";
const umbral = 40;
const desde = new Date("2025-01-01T00:00:00Z");
const hasta = new Date("2026-01-02T00:00:00Z");

const base = db;

const resultados = base.lecturas.find(
  {
    zona_id: zonaId,
    tipo_sensor: tipoSensor,
    variable,
    unidad,
    fecha_utc: { $gte: desde, $lt: hasta },
    valor: { $gt: umbral }
  },
  {
    _id: 1,
    sensor_id: 1,
    zona_id: 1,
    tipo_sensor: 1,
    variable: 1,
    valor: 1,
    unidad: 1,
    fecha_utc: 1
  }
).sort({ fecha_utc: 1, _id: 1 }).toArray();

print(`Lecturas encontradas: ${resultados.length}`);
printjson(resultados);
