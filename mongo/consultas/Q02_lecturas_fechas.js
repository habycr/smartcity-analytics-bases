// Q02: lecturas desde una fecha_utc inclusive hasta otra exclusiva.
// Las fechas se interpretan en UTC.
const desde = new Date("2025-01-01T00:00:00Z");
const hasta = new Date("2025-01-02T00:00:00Z");

if (desde >= hasta) {
  throw new Error("La fecha_utc desde debe ser anterior a hasta");
}

const base = db;

const resultados = base.lecturas.find(
  {
    fecha_utc: {
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
    fecha_utc: 1
  }
).sort({ fecha_utc: 1, sensor_id: 1, _id: 1 }).toArray();

print(`Desde: ${desde.toISOString()}`);
print(`Hasta (exclusiva): ${hasta.toISOString()}`);
print(`Lecturas encontradas: ${resultados.length}`);
printjson(resultados);
