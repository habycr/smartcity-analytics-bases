// Sprint 1 - Edward: modelo y validadores MongoDB.
// No elimina datos existentes. Base por defecto: smartcity_demo para pruebas.
// Para produccion, configurar SMARTCITY_DB=smartcity antes de ejecutar.
const nombreBD = (typeof process !== 'undefined' && process.env.SMARTCITY_DB) || 'smartcity_demo';
const base = db.getSiblingDB(nombreBD);
const numero = ['double', 'decimal', 'int', 'long'];
const fecha = { bsonType: 'date', description: 'Fecha UTC almacenada como BSON Date' };
const cadena = { bsonType: 'string', minLength: 1 };
const booleano = { bsonType: 'bool' };
const propiedadesBase = { fuente: cadena, sintetico: booleano, fecha_utc: fecha };
const definiciones = {
  lecturas: {
    required: ['sensor_id','zona_id','tipo_sensor','variable','unidad','valor','fecha_utc','fuente','sintetico'],
    properties: {
      ...propiedadesBase, sensor_id: cadena, zona_id: cadena, tipo_sensor: cadena,
      variable: cadena, unidad: cadena, valor: { bsonType: numero },
      metadata: { bsonType: 'object' },
      procedencia: { bsonType: 'object' },
      calidad: { bsonType: 'object' }
    }
  },
  eventos: {
    required: ['sensor_id','zona_id','categoria','severidad','fecha_utc','fuente','sintetico'],
    properties: {
      ...propiedadesBase, sensor_id: cadena, zona_id: cadena,
      categoria: cadena, severidad: { enum: ['informativa','advertencia','critica'] },
      lectura_id: { bsonType: ['string','objectId'] },
      detalle: { bsonType: 'object' }, descripcion: { bsonType: 'string' }
    }
  },
  alertas: {
    required: ['sensor_id','zona_id','variable','valor','umbral','unidad','estado','fecha_utc','fuente','sintetico'],
    properties: {
      ...propiedadesBase, sensor_id: cadena, zona_id: cadena, variable: cadena,
      valor: { bsonType: numero }, umbral: { bsonType: numero }, unidad: cadena,
      estado: { enum: ['pendiente','atendida','descartada'] },
      evento_id: { bsonType: ['string','objectId'] },
      detalle: { bsonType: 'object' }
    }
  },
  incidentes: {
    required: ['zona_id','categoria','descripcion','fecha_utc','fuente','sintetico'],
    properties: {
      ...propiedadesBase, zona_id: cadena, categoria: cadena,
      descripcion: cadena, sensor_id: cadena,
      detalle: { bsonType: 'object' }
    }
  }
};
for (const [nombre, definicion] of Object.entries(definiciones)) {
  const validator = { $jsonSchema: { bsonType: 'object', ...definicion } };
  if (!base.getCollectionNames().includes(nombre)) {
    base.createCollection(nombre, { validator, validationLevel: 'strict', validationAction: 'error' });
    print('Creada: ' + nombre);
  } else {
    base.runCommand({ collMod: nombre, validator, validationLevel:'strict', validationAction:'error' });
    print('Validador actualizado: ' + nombre);
  }
}
print('Base: ' + nombreBD + '; colecciones: ' + base.getCollectionNames().join(', '));
