const base = db;

// Q01: igualdad por sensor y orden por fecha_utc e identificador.
base.lecturas.createIndex(
  { sensor_id: 1, fecha_utc: 1, _id: 1 },
  { name: "idx_lecturas_sensor_fecha" }
);

// Q02: busqueda por rango de fechas.
base.lecturas.createIndex(
  { fecha_utc: 1 },
  { name: "idx_lecturas_fecha" }
);

// Q09: igualdad por variable/unidad y rango de fechas.
base.lecturas.createIndex(
  { variable: 1, unidad: 1, fecha_utc: 1 },
  { name: "idx_lecturas_variable_unidad_fecha" }
);

// Q10: igualdades seguidas del rango temporal.
// El filtro por valor se evalua sobre las lecturas seleccionadas.
base.lecturas.createIndex(
  {
    zona_id: 1,
    tipo_sensor: 1,
    variable: 1,
    unidad: 1,
    fecha_utc: 1
  },
  { name: "idx_lecturas_filtros_fecha" }
);

// Q04: igualdad por severidad y orden por fecha_utc e identificador.
base.eventos.createIndex(
  { severidad: 1, fecha_utc: 1, _id: 1 },
  { name: "idx_eventos_severidad_fecha" }
);

for (const nombre of ["lecturas", "eventos"]) {
  print(`Indices de ${nombre}:`);
  printjson(base.getCollection(nombre).getIndexes());
}
