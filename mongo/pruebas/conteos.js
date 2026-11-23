const nombreBD = (typeof process !== 'undefined' && process.env.SMARTCITY_DB) || 'smartcity_demo';
const base=db.getSiblingDB(nombreBD);
print('Base: '+nombreBD);
for(const nombre of ['lecturas','eventos','alertas','incidentes']) {
 print(nombre+': '+base.getCollection(nombre).countDocuments({}));
 printjson(base.getCollection(nombre).aggregate([{$group:{_id:'$sintetico',n:{$sum:1}}},{$sort:{_id:1}}]).toArray());
}
print('Ejemplo de documento:');printjson(base.lecturas.findOne());
