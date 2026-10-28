// Q09: evolucion diaria de una variable por zona, en UTC.
const variable = "pm25";
const unidad = "µg/m³";
const desde = new Date("2025-01-01T00:00:00Z");
const hasta = new Date("2025-01-03T00:00:00Z");

const base = db;

const resultados = base.lecturas.aggregate([
  {
    $match: {
      variable,
      unidad,
      fecha_utc: { $gte: desde, $lt: hasta }
    }
  },
  {
    $group: {
      _id: {
        dia: {
          $dateToString: {
            format: "%Y-%m-%d",
            date: "$fecha_utc",
            timezone: "UTC"
          }
        },
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
      dia: "$_id.dia",
      zona_id: "$_id.zona_id",
      variable: "$_id.variable",
      unidad: "$_id.unidad",
      promedio: 1,
      cantidad: 1
    }
  },
  {
    $sort: { dia: 1, zona_id: 1, variable: 1, unidad: 1 }
  }
]).toArray();

print(`Evolucion diaria de ${variable} por zona (UTC):`);
printjson(resultados);
