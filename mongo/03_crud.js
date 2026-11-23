// CRUD: siete operaciones requeridas, SOLO identificadores DEMO-CRUD-.
// Se ejecuta por defecto en smartcity_demo, sin modificar documentos EPA.
const nombreBD = (typeof process !== 'undefined' && process.env.SMARTCITY_DB) || 'smartcity_demo';
if (nombreBD === 'smartcity') throw Error('CRUD de demostracion bloqueado en base de produccion smartcity');
const base = db.getSiblingDB(nombreBD);
const col = base.lecturas;
const origen = {sensor_id:'DEMO-S001',zona_id:'DEMO-Z001',tipo_sensor:'particulas',variable:'pm25',unidad:'µg/m³',fuente:'DEMO CRUD',sintetico:true};
col.deleteMany({_id:{$in:['DEMO-CRUD-001','DEMO-CRUD-002','DEMO-CRUD-003']}}); // limpieza previa
print('1. insertOne');
printjson(col.insertOne({...origen,_id:'DEMO-CRUD-001',valor:10,fecha_utc:new Date('2025-02-01T00:00:00Z')}));
print('2. insertMany');
printjson(col.insertMany([
 {...origen,_id:'DEMO-CRUD-002',valor:11,fecha_utc:new Date('2025-02-02T00:00:00Z')},
 {...origen,_id:'DEMO-CRUD-003',valor:12,fecha_utc:new Date('2025-02-03T00:00:00Z')}
]));
print('3. find: todos los documentos del CRUD');
printjson(col.find({_id:{$regex:'^DEMO-CRUD-'}}).sort({fecha_utc:1}).toArray());
print('4. findOne');
printjson(col.findOne({_id:'DEMO-CRUD-001'}));
print('5. updateOne');
printjson(col.updateOne({_id:'DEMO-CRUD-001'},{$set:{valor:25}}));
print('6. updateMany');
printjson(col.updateMany({_id:{$in:['DEMO-CRUD-002','DEMO-CRUD-003']}},{$set:{'metadata.revisado':true}}));
print('7. deleteOne');
printjson(col.deleteOne({_id:'DEMO-CRUD-003'}));
print('Resultados posteriores:');
printjson(col.find({_id:{$regex:'^DEMO-CRUD-'}}).toArray());
print('Limpieza de demostracion:');
printjson(col.deleteMany({_id:{$regex:'^DEMO-CRUD-'}}));
print('Total restante DEMO-CRUD: '+col.countDocuments({_id:{$regex:'^DEMO-CRUD-'}}));
