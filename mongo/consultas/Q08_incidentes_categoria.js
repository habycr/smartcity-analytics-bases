// Q08: cantidad de incidentes registrados por categoria.
const base = db;

const resultados = base.incidentes.aggregate([
  {
    $group: {
      _id: "$categoria",
      cantidad_incidentes: { $sum: 1 }
    }
  },
  {
    $project: {
      _id: 0,
      categoria: "$_id",
      cantidad_incidentes: 1
    }
  },
  {
    $sort: { cantidad_incidentes: -1, categoria: 1 }
  }
]).toArray();

print("Incidentes registrados por categoria:");
printjson(resultados);
