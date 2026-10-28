// Q04: eventos clasificados con severidad critica.
const base = db;

const resultados = base.eventos.find(
  { severidad: "critica" },
  {
    _id: 1,
    sensor_id: 1,
    zona_id: 1,
    lectura_id: 1,
    categoria: 1,
    severidad: 1,
    fecha_utc: 1
  }
).sort({ fecha_utc: 1, _id: 1 }).toArray();

print(`Eventos criticos encontrados: ${resultados.length}`);
printjson(resultados);
