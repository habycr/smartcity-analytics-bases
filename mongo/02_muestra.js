// Documentos sintéticos: solo para demostracion. No son observaciones reales EPA.
// Requiere ejecutar antes 01_colecciones.js. Base: smartcity_demo por defecto.
const nombreBD = (typeof process !== 'undefined' && process.env.SMARTCITY_DB) || 'smartcity_demo';
const base = db.getSiblingDB(nombreBD);
const zonaA='DEMO-Z001', zonaB='DEMO-Z002';
const lecturas = [
 ['DEMO-L001','DEMO-S001',zonaA,'pm25',10,'2025-01-01T12:00:00Z'],
 ['DEMO-L002','DEMO-S001',zonaA,'pm25',50,'2025-01-02T12:00:00Z'],
 ['DEMO-L003','DEMO-S002',zonaB,'pm25',20,'2025-01-01T12:00:00Z'],
 ['DEMO-L004','DEMO-S002',zonaB,'pm25',60,'2025-01-02T12:00:00Z'],
 ['DEMO-L005','DEMO-S003',zonaA,'pm10',30,'2025-01-01T12:00:00Z'],
 ['DEMO-L006','DEMO-S003',zonaA,'pm10',65,'2025-01-02T12:00:00Z'],
 ['DEMO-L007','DEMO-S004',zonaB,'pm10',20,'2025-01-01T12:00:00Z'],
 ['DEMO-L008','DEMO-S004',zonaB,'pm10',70,'2025-01-02T12:00:00Z']
].map(([id,sensor,zona,variable,valor,instante]) => ({
 _id:id,sensor_id:sensor,zona_id:zona,tipo_sensor:'particulas',variable,
 valor,unidad:'µg/m³',fecha_utc:new Date(instante),fuente:'DEMO sintético',sintetico:true,
 metadata:variable==='pm25' ? { tipo_muestra:'horaria',modelo:'ejemplo' } : {tipo_muestra:'horaria',calibracion:'simulada'}
}));
const eventos = [
 {_id:'DEMO-E001',sensor_id:'DEMO-S001',zona_id:zonaA,lectura_id:'DEMO-L002',categoria:'contaminacion',severidad:'critica',fecha_utc:new Date('2025-01-02T12:00:00Z'),fuente:'DEMO sintético',sintetico:true},
 {_id:'DEMO-E002',sensor_id:'DEMO-S002',zona_id:zonaB,lectura_id:'DEMO-L004',categoria:'contaminacion',severidad:'critica',fecha_utc:new Date('2025-01-02T12:00:00Z'),fuente:'DEMO sintético',sintetico:true},
 {_id:'DEMO-E003',sensor_id:'DEMO-S003',zona_id:zonaA,categoria:'mantenimiento',severidad:'informativa',fecha_utc:new Date('2025-01-03T09:00:00Z'),fuente:'DEMO sintético',sintetico:true}
];
const alertas = [
 {_id:'DEMO-A001',evento_id:'DEMO-E001',sensor_id:'DEMO-S001',zona_id:zonaA,variable:'pm25',valor:50,umbral:40,unidad:'µg/m³',estado:'pendiente',fecha_utc:new Date('2025-01-02T12:01:00Z'),fuente:'DEMO sintético',sintetico:true},
 {_id:'DEMO-A002',evento_id:'DEMO-E002',sensor_id:'DEMO-S002',zona_id:zonaB,variable:'pm25',valor:60,umbral:40,unidad:'µg/m³',estado:'pendiente',fecha_utc:new Date('2025-01-02T12:01:00Z'),fuente:'DEMO sintético',sintetico:true}
];
const incidentes = [
 {_id:'DEMO-I001',zona_id:zonaA,categoria:'ambiental',descripcion:'Reporte de humo ficticio',fecha_utc:new Date('2025-01-02T13:00:00Z'),fuente:'DEMO sintético',sintetico:true},
 {_id:'DEMO-I002',zona_id:zonaB,categoria:'ambiental',descripcion:'Reporte de polvo ficticio',fecha_utc:new Date('2025-01-02T14:00:00Z'),fuente:'DEMO sintético',sintetico:true},
 {_id:'DEMO-I003',zona_id:zonaA,categoria:'infraestructura',descripcion:'Luminaria ficticia averiada',fecha_utc:new Date('2025-01-03T18:00:00Z'),fuente:'DEMO sintético',sintetico:true}
];
for (const [nombre,documentos] of Object.entries({lecturas,eventos,alertas,incidentes})) {
 for (const documento of documentos) {
   base.getCollection(nombre).replaceOne({_id:documento._id},documento,{upsert:true});
 }
 print(`${nombre}: ${base.getCollection(nombre).countDocuments({sintetico:true})} documentos sintéticos`);
}
print('Base de muestra: ' + nombreBD);
