// Q03: máximos y mínimos registrados por variable y unidad.
const base = db;

const resultados = base.lecturas.aggregate([
  {
    $group: {
      _id: {
        variable: "$variable",
        unidad: "$unidad"
      },
      minimo: { $min: "$valor" },
      maximo: { $max: "$valor" },
      cantidad: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      variable: "$_id.variable",
      unidad: "$_id.unidad",
      minimo: 1,
      maximo: 1,
      cantidad: 1
    }
  },
  {
    $sort: { variable: 1, unidad: 1 }
  }
]).toArray();

print("Maximos y minimos por variable y unidad:");
printjson(resultados);
