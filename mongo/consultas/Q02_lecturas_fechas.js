// Q02: lecturas desde una fecha inclusive hasta otra exclusiva.
// Las fechas se interpretan en UTC.
const desde = new Date("2026-10-01T00:00:00Z");
const hasta = new Date("2026-10-02T00:00:00Z");

if (desde >= hasta) {
  throw new Error("La fecha desde debe ser anterior a hasta");
}

const base = db.getSiblingDB("smartcity");

const resultados = base.lecturas.find(
  {
    fecha: {
      $gte: desde,
      $lt: hasta
    }
  },
  {
    _id: 0,
    sensor_id: 1,
    zona_id: 1,
    variable: 1,
    valor: 1,
    unidad: 1,
    fecha: 1
  }
).sort({ fecha: 1, sensor_id: 1, _id: 1 }).toArray();

print(`Desde: ${desde.toISOString()}`);
print(`Hasta (exclusiva): ${hasta.toISOString()}`);
print(`Lecturas encontradas: ${resultados.length}`);
printjson(resultados);
