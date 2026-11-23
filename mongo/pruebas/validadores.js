// Debe rechazar un dato sin sensor y otro con fecha como string.
const nombreBD = (typeof process !== 'undefined' && process.env.SMARTCITY_DB) || 'smartcity_demo';
if (nombreBD === 'smartcity') throw Error('Pruebas invalidas bloqueadas en produccion');
const base=db.getSiblingDB(nombreBD);
const valido={_id:'DEMO-VALID-001',sensor_id:'DEMO-S001',zona_id:'DEMO-Z001',tipo_sensor:'particulas',variable:'pm25',valor:12.5,unidad:'µg/m³',fecha_utc:new Date('2025-01-01T00:00:00Z'),fuente:'DEMO prueba',sintetico:true};
let rechazos=0;
for (const [etiqueta,doc] of [
 ['sin sensor_id',(()=>{const d={...valido,_id:'DEMO-VALID-002'};delete d.sensor_id;return d})()],
 ['fecha_utc string',{...valido,_id:'DEMO-VALID-003',fecha_utc:'2025-01-01T00:00:00Z'}]
]) {
 try {base.lecturas.insertOne(doc);print('ERROR: aceptado '+etiqueta);} catch(e) {rechazos++;print('CORRECTO: rechazado '+etiqueta);}
 base.lecturas.deleteOne({_id:doc._id});
}
try {base.lecturas.replaceOne({_id:valido._id},valido,{upsert:true});print('CORRECTO: lectura valida aceptada');}
finally {base.lecturas.deleteOne({_id:valido._id});}
if(rechazos!==2) throw Error('No se rechazaron los 2 documentos invalidos');
print('OK: 2/2 validaciones negativas');
