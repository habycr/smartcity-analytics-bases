// Datos sintéticos para desarrollo. No representan observaciones reales.
const base = db.getSiblingDB("smartcity");

// Cada variable tiene una unidad fija.
// Las fechas se almacenan como BSON Date en UTC.
const lecturas = [
  ["L001", "S001", "Z001", "temperatura", 20, "°C", "2026-10-01T12:00:00Z"],
  ["L002", "S001", "Z001", "temperatura", 30, "°C", "2026-10-02T12:00:00Z"],
  ["L003", "S002", "Z002", "temperatura", 24, "°C", "2026-10-01T12:00:00Z"],
  ["L004", "S002", "Z002", "temperatura", 28, "°C", "2026-10-02T12:00:00Z"],
  ["L005", "S003", "Z001", "pm25", 10, "µg/m³", "2026-10-01T12:00:00Z"],
  ["L006", "S003", "Z001", "pm25", 50, "µg/m³", "2026-10-02T12:00:00Z"],
  ["L007", "S004", "Z002", "pm25", 20, "µg/m³", "2026-10-01T12:00:00Z"],
  ["L008", "S004", "Z002", "pm25", 60, "µg/m³", "2026-10-02T12:00:00Z"]
].map(([id, sensor, zona, variable, valor, unidad, fecha]) => ({
  _id: id,
  sensor_id: sensor,
  zona_id: zona,
  tipo_sensor: variable === "temperatura"
    ? "termometro"
    : "particulas",
  variable,
  valor,
  unidad,
  fecha: new Date(fecha),
  fuente: "muestra_desarrollo",
  sintetico: true
}));

const eventos = [
  {
    _id: "E001",
    sensor_id: "S003",
    zona_id: "Z001",
    lectura_id: "L006",
    categoria: "contaminacion",
    severidad: "critica",
    fecha: new Date("2026-10-02T12:00:00Z")
  },
  {
    _id: "E002",
    sensor_id: "S004",
    zona_id: "Z002",
    lectura_id: "L008",
    categoria: "contaminacion",
    severidad: "critica",
    fecha: new Date("2026-10-02T12:00:00Z")
  },
  {
    _id: "E003",
    sensor_id: "S001",
    zona_id: "Z001",
    categoria: "mantenimiento",
    severidad: "informativa",
    fecha: new Date("2026-10-03T09:00:00Z")
  }
];

// Umbral ficticio de desarrollo: no es un límite normativo.
const alertas = [
  {
    _id: "A001",
    evento_id: "E001",
    sensor_id: "S003",
    zona_id: "Z001",
    variable: "pm25",
    valor: 50,
    umbral: 40,
    unidad: "µg/m³",
    estado: "pendiente",
    fecha: new Date("2026-10-02T12:01:00Z")
  },
  {
    _id: "A002",
    evento_id: "E002",
    sensor_id: "S004",
    zona_id: "Z002",
    variable: "pm25",
    valor: 60,
    umbral: 40,
    unidad: "µg/m³",
    estado: "pendiente",
    fecha: new Date("2026-10-02T12:01:00Z")
  }
];

const incidentes = [
  {
    _id: "I001",
    zona_id: "Z001",
    categoria: "ambiental",
    descripcion: "Reporte ficticio de acumulacion de humo",
    fecha: new Date("2026-10-02T13:00:00Z")
  },
  {
    _id: "I002",
    zona_id: "Z002",
    categoria: "ambiental",
    descripcion: "Reporte ficticio de polvo",
    fecha: new Date("2026-10-02T14:00:00Z")
  },
  {
    _id: "I003",
    zona_id: "Z001",
    categoria: "infraestructura",
    descripcion: "Reporte ficticio de luminaria averiada",
    fecha: new Date("2026-10-03T18:00:00Z")
  }
];

// Actualiza o inserta por _id: repetir el script no duplica la muestra.
// No borra otros documentos que existan en las colecciones.
for (const [nombre, documentos] of Object.entries({
  lecturas,
  eventos,
  alertas,
  incidentes
})) {
  for (const documento of documentos) {
    base.getCollection(nombre).replaceOne(
      { _id: documento._id },
      {
        ...documento,
        fuente: "muestra_desarrollo",
        sintetico: true
      },
      { upsert: true }
    );
  }

  print(`${nombre}: ${documentos.length} documentos de muestra cargados`);
}
