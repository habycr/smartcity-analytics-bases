// Dataset sintetico exclusivo para evaluar el acceso por indice.
// No representa observaciones reales ni reemplaza la carga de Edward.
const base = db.getSiblingDB("smartcity_rendimiento");
const nombreColeccion = "lecturas_benchmark_v1";
const total = 500000;
const lote = 5000;

// La generacion solo se ejecuta si la coleccion esta vacia.
const coleccion = base.getCollection(nombreColeccion);
const existentes = coleccion.countDocuments({});

if (existentes === 0) {
  print(`Generando ${total} lecturas sinteticas...`);

  const inicio = Date.UTC(2026, 0, 1);

  for (let offset = 0; offset < total; offset += lote) {
    const documentos = [];

    for (let i = offset; i < Math.min(offset + lote, total); i++) {
      const numeroSensor = i % 1000;

      documentos.push({
        _id: i,
        sensor_id: `S${String(numeroSensor).padStart(4, "0")}`,
        zona_id: `Z${String(numeroSensor % 20).padStart(2, "0")}`,
        tipo_sensor: "termometro",
        variable: "temperatura",
        unidad: "°C",
        valor: 15 + (i % 250) / 10,
        fecha: new Date(inicio + i * 60000),
        fuente: "benchmark_sintetico_v1",
        sintetico: true
      });
    }

    coleccion.insertMany(documentos);

    if ((offset + documentos.length) % 100000 === 0) {
      print(`Cargados: ${offset + documentos.length}`);
    }
  }
} else if (existentes !== total) {
  throw new Error(
    `La coleccion contiene ${existentes} documentos, se esperaban ${total}. ` +
    "La carga puede estar incompleta. No se modificaron los datos existentes."
  );
}

coleccion.createIndex(
  { sensor_id: 1, fecha: 1, _id: 1 },
  { name: "idx_sensor_fecha" }
);

const filtro = { sensor_id: "S0001" };
const orden = { fecha: 1, _id: 1 };

function consultar(hint) {
  return coleccion.find(filtro).sort(orden).hint(hint);
}

function medir(hint) {
  const explicacion = consultar(hint).explain("executionStats");
  const s = explicacion.executionStats;

  return {
    resultados: s.nReturned,
    documentosExaminados: s.totalDocsExamined,
    clavesExaminadas: s.totalKeysExamined,
    tiempoMs: s.executionTimeMillis
  };
}

// Comprobar que ambas estrategias devuelven exactamente los mismos IDs.
const idsCompleto = consultar({ $natural: 1 }).toArray().map(x => x._id);
const idsIndice = consultar("idx_sensor_fecha").toArray().map(x => x._id);

if (
  idsCompleto.length !== 500 ||
  JSON.stringify(idsCompleto) !== JSON.stringify(idsIndice)
) {
  throw new Error("Las estrategias no devolvieron los 500 resultados esperados");
}

print("[PASS] Ambas estrategias devuelven los mismos 500 documentos");

// Calentamiento: estas ejecuciones no se incluyen en las mediciones.
medir({ $natural: 1 });
medir("idx_sensor_fecha");

const completo = [];
const indice = [];

// Alternar el orden para reducir el sesgo de ejecutar siempre uno primero.
for (let i = 0; i < 5; i++) {
  if (i % 2 === 0) {
    completo.push(medir({ $natural: 1 }));
    indice.push(medir("idx_sensor_fecha"));
  } else {
    indice.push(medir("idx_sensor_fecha"));
    completo.push(medir({ $natural: 1 }));
  }
}

function mediana(valores) {
  const ordenados = [...valores].sort((a, b) => a - b);
  return ordenados[Math.floor(ordenados.length / 2)];
}

const reporte = {
  fechaEjecucion: new Date(),
  versionMongoDB: base.version(),
  base: base.getName(),
  coleccion: nombreColeccion,
  documentos: coleccion.countDocuments({}),
  sensores: 1000,
  documentosPorSensor: 500,
  filtro,
  orden,
  repeticiones: 5,
  recorridoCompleto: {
    ejecuciones: completo,
    medianaTiempoMs: mediana(completo.map(x => x.tiempoMs))
  },
  conIndice: {
    ejecuciones: indice,
    medianaTiempoMs: mediana(indice.map(x => x.tiempoMs))
  },
  limites: [
    "Datos sinteticos de distribucion uniforme.",
    "Ejecucion local con calentamiento; no mide cache fria.",
    "hint fuerza cada estrategia; no evalua la eleccion automatica.",
    "Los tiempos dependen del equipo y su carga.",
    "No mide el costo de mantener indices durante escrituras.",
    "No sustituye la validacion con las fuentes finales."
  ]
};

printjson(reporte);
