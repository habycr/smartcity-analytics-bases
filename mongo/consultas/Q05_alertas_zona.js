// Q05: cantidad de alertas emitidas por zona.
const base = db.getSiblingDB("smartcity");

const resultados = base.alertas.aggregate([
  {
    $group: {
      _id: "$zona_id",
      cantidad_alertas: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      zona_id: "$_id",
      cantidad_alertas: 1
    }
  },
  {
    $sort: { cantidad_alertas: -1, zona_id: 1 }
  }
]).toArray();

print("Alertas emitidas por zona:");
printjson(resultados);
