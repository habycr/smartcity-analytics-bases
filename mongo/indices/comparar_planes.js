// Comparacion controlada de acceso para Q01.
// Los hints fuerzan cada estrategia; no muestran la eleccion automatica.
const base = db;

const filtro = { sensor_id: "EPA-01-003-0010-88101-3" };
const orden = { fecha_utc: 1, _id: 1 };

function comparar(nombre, hint) {
  const explicacion = base.lecturas
    .find(filtro)
    .sort(orden)
    .hint(hint)
    .explain("executionStats");

  const stats = explicacion.executionStats;

  print(`\n${nombre}`);
  printjson({
    resultados: stats.nReturned,
    documentosExaminados: stats.totalDocsExamined,
    clavesExaminadas: stats.totalKeysExamined,
    tiempoMilisegundos: stats.executionTimeMillis
  });

  print("Plan de ejecucion:");
  printjson(explicacion.queryPlanner.winningPlan);
}

comparar("RECORRIDO COMPLETO", { $natural: 1 });
comparar("CON INDICE", "idx_lecturas_sensor_fecha");
