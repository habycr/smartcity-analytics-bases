// Verifica exclusivamente los documentos de la muestra.
// No modifica ni borra datos.
const base = db.getSiblingDB("smartcity");
const muestra = {
  fuente: "muestra_desarrollo",
  sintetico: true
};

let aprobadas = 0;

function verificar(nombre, obtenido, esperado) {
  if (JSON.stringify(obtenido) !== JSON.stringify(esperado)) {
    throw new Error(
      `${nombre}: esperado ${JSON.stringify(esperado)}, ` +
      `obtenido ${JSON.stringify(obtenido)}`
    );
  }

  print(`[PASS] ${nombre}`);
  aprobadas++;
}

// Conteos de la muestra.
for (const [coleccion, cantidad] of [
  ["lecturas", 8],
  ["eventos", 3],
  ["alertas", 2],
  ["incidentes", 3]
]) {
  verificar(
    `Cantidad en ${coleccion}`,
    base.getCollection(coleccion).countDocuments(muestra),
    cantidad
  );
}

// Q01: filtro por sensor.
verificar(
  "Q01: lecturas de S001",
  base.lecturas.countDocuments({ ...muestra, sensor_id: "S001" }),
  2
);

// Q02: rango desde inclusive hasta exclusivo.
verificar(
  "Q02: lecturas del primer dia",
  base.lecturas.countDocuments({
    ...muestra,
    fecha: {
      $gte: new Date("2026-10-01T00:00:00Z"),
      $lt: new Date("2026-10-02T00:00:00Z")
    }
  }),
  4
);

// Q03: extremos conocidos.
const extremos = base.lecturas.aggregate([
  { $match: muestra },
  {
    $group: {
      _id: { variable: "$variable", unidad: "$unidad" },
      minimo: { $min: "$valor" },
      maximo: { $max: "$valor" }
    }
  },
  { $sort: { "_id.variable": 1, "_id.unidad": 1 } }
]).toArray();

verificar(
  "Q03: extremos",
  extremos.map(x => [x._id.variable, x.minimo, x.maximo]),
  [["pm25", 10, 60], ["temperatura", 20, 30]]
);

// Q04: eventos criticos.
verificar(
  "Q04: eventos criticos",
  base.eventos.countDocuments({ ...muestra, severidad: "critica" }),
  2
);

// Q10: filtros multiples.
verificar(
  "Q10: lectura que cumple todos los filtros",
  base.lecturas.find({
    ...muestra,
    zona_id: "Z002",
    tipo_sensor: "particulas",
    variable: "pm25",
    unidad: "µg/m³",
    fecha: {
      $gte: new Date("2026-10-01T00:00:00Z"),
      $lt: new Date("2026-10-03T00:00:00Z")
    },
    valor: { $gt: 40 }
  }).toArray().map(x => x._id).sort(),
  ["L008"]
);

// Casos sin resultados.
verificar(
  "Sensor inexistente",
  base.lecturas.countDocuments({
    ...muestra,
    sensor_id: "SENSOR-INEXISTENTE"
  }),
  0
);

verificar(
  "Periodo sin lecturas",
  base.lecturas.countDocuments({
    ...muestra,
    fecha: {
      $gte: new Date("2026-09-01T00:00:00Z"),
      $lt: new Date("2026-09-02T00:00:00Z")
    }
  }),
  0
);

print(`\n${aprobadas} comprobaciones aprobadas.`);
