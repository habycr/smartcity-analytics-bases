// SmartCity Analytics / Edward - eventos, alertas e incidentes demostrativos.
// Este script NO crea eventos/alertas/incidentes reales de EPA.
// Usa la base indicada en la URI, sin modificar las lecturas.
// Es idempotente: cada documento de DEMO usa un _id estable.
const base = db;
const FUENTE = 'DEMO - reglas ilustrativas sobre EPA AQS 2025';
const campos = {
  _id: 1, sensor_id: 1, zona_id: 1, fecha_utc: 1,
  valor: 1, variable: 1, unidad: 1
};
const configuracion = [
  { variable: 'pm25', umbral: '40', maximo: 5 },
  { variable: 'pm10', umbral: '80', maximo: 5 }
];

if (!base.getCollectionNames().includes('lecturas') ||
    base.lecturas.countDocuments({ sintetico: false }) === 0) {
  throw new Error('No hay lecturas EPA reales en la base seleccionada.');
}
for (const nombre of ['eventos','alertas','incidentes']) {
  if (!base.getCollectionNames().includes(nombre)) {
    throw new Error('Falta la coleccion ' + nombre + '. Ejecutar 01_colecciones.js primero.');
  }
}

let totalEventos = 0;
let totalAlertas = 0;
const sensoresDemostracion = [];
for (const regla of configuracion) {
  const umbral = NumberDecimal(regla.umbral);
  const lecturas = base.lecturas.find(
    { variable: regla.variable, valor: { $gt: umbral }, sintetico: false },
    campos
  ).sort({ _id: 1 }).limit(regla.maximo).toArray();

  if (lecturas.length === 0) {
    print('AVISO: sin lecturas para la regla demostrativa ' + regla.variable);
    continue;
  }
  for (const lectura of lecturas) {
    const eventoId = 'DEMO-EVENTO-' + lectura._id;
    const alertaId = 'DEMO-ALERTA-' + lectura._id;
    const evento = {
      _id: eventoId,
      sensor_id: lectura.sensor_id,
      zona_id: lectura.zona_id,
      lectura_id: lectura._id,
      categoria: 'contaminacion', severidad: 'critica',
      fecha_utc: lectura.fecha_utc,
      fuente: FUENTE, sintetico: true,
      descripcion: 'Evento simulado por superacion de un umbral ilustrativo',
      detalle: { variable: regla.variable, umbral: umbral,
        regla: 'valor > umbral', origen_lectura: 'EPA AQS hourly 2025',
        aviso: 'No representa una determinacion oficial de riesgo' }
    };
    const alerta = {
      _id: alertaId, evento_id: eventoId,
      sensor_id: lectura.sensor_id, zona_id: lectura.zona_id,
      variable: regla.variable, valor: lectura.valor, umbral: umbral,
      unidad: lectura.unidad, estado: 'pendiente',
      fecha_utc: lectura.fecha_utc,
      fuente: FUENTE, sintetico: true,
      detalle: { regla: 'valor > umbral', finalidad: 'demostracion academica',
        aviso: 'Alerta simulada, no emitida por EPA ni por una municipalidad' }
    };
    base.eventos.replaceOne({ _id: eventoId }, evento, { upsert: true });
    base.alertas.replaceOne({ _id: alertaId }, alerta, { upsert: true });
    totalEventos++;
    totalAlertas++;
    sensoresDemostracion.push(lectura);
  }
}

const escenarios = [
  { categoria: 'ambiental', descripcion: 'Reporte hipotetico de polvo en una zona urbana' },
  { categoria: 'infraestructura', descripcion: 'Reporte hipotetico de equipo urbano averiado' },
  { categoria: 'ambiental', descripcion: 'Reporte hipotetico de humo en un sector urbano' }
];
for (let i = 0; i < escenarios.length; i++) {
  const referencia = sensoresDemostracion[i % sensoresDemostracion.length];
  if (!referencia) throw new Error('No se encontraron lecturas para crear incidentes de demostracion.');
  base.incidentes.replaceOne(
    { _id: `DEMO-INCIDENTE-${String(i + 1).padStart(3, '0')}` },
    {
      _id: `DEMO-INCIDENTE-${String(i + 1).padStart(3, '0')}`,
      zona_id: referencia.zona_id,
      sensor_id: referencia.sensor_id,
      categoria: escenarios[i].categoria,
      descripcion: escenarios[i].descripcion,
      fecha_utc: referencia.fecha_utc,
      fuente: FUENTE, sintetico: true,
      detalle: { tipo: 'escenario_ficticio', evidencia_real: false,
        aviso: 'Incidente academico simulado, no registrado por EPA' }
    },
    { upsert: true }
  );
}
print('Lecturas EPA intactas: ' + base.lecturas.countDocuments({ sintetico: false }));
print('Eventos DEMO usados en esta ejecucion: ' + totalEventos);
print('Alertas DEMO usadas en esta ejecucion: ' + totalAlertas);
print('Incidentes DEMO creados/actualizados: ' + escenarios.length);
print('Conteos de las colecciones:');
for (const n of ['lecturas', 'eventos', 'alertas', 'incidentes']) {
  print('  ' + n + ': ' + base.getCollection(n).countDocuments({}));
}
