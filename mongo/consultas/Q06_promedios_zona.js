// Q06: promedio por zona, variable y unidad.
const base = db.getSiblingDB("smartcity");

const resultados = base.lecturas.aggregate([
  {
    $group: {
      _id: {
        zona_id: "$zona_id",
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
      zona_id: "$_id.zona_id",
      variable: "$_id.variable",
      unidad: "$_id.unidad",
      promedio: 1,
      cantidad: 1
    }
  },
  {
    $sort: { zona_id: 1, variable: 1, unidad: 1 }
  }
]).toArray();

print("Promedios por zona, variable y unidad:");
printjson(resultados);
