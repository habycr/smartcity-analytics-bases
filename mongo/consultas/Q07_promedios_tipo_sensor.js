// Q07: promedio por tipo de sensor, variable y unidad.
const base = db.getSiblingDB("smartcity");

const resultados = base.lecturas.aggregate([
  {
    $group: {
      _id: {
        tipo_sensor: "$tipo_sensor",
        variable: "$variable",
        unidad: "$unidad"
      },
      promedio: { $avg: "$valor" },
      cantidad: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      tipo_sensor: "$_id.tipo_sensor",
      variable: "$_id.variable",
      unidad: "$_id.unidad",
      promedio: 1,
      cantidad: 1
    }
  },
  {
    $sort: { tipo_sensor: 1, variable: 1, unidad: 1 }
  }
]).toArray();

print("Promedios por tipo de sensor, variable y unidad:");
printjson(resultados);
