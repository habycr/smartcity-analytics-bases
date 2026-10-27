-- SmartCity Analytics | Sprint 1 | PostgreSQL 16
-- Datos exclusivamente SINTETICOS y de demostracion (no son observaciones EPA).
-- Ejecutar despues de 01_schema.sql; se puede ejecutar varias veces sin duplicar datos.
-- IDs numéricos de ejemplo reservados: categorias/organismos/usuarios/variables >= 900001;
-- mediciones >= 9000001. No utilizar estas reservas en carga real.
-- ATENCION: las fechas de instalacion, estados, personas y ubicaciones son inventados.
-- Este script NO debe usarse como evidencia de calidad de fuentes reales.

BEGIN;

INSERT INTO public.ubicacion (id_ubicacion, nombre_zona, distrito, latitud, longitud) VALUES
 ('DEMO-Z001', 'Zona demostrativa Centro', 'Distrito Demo A', 9.864000, -83.914000),
 ('DEMO-Z002', 'Zona demostrativa Norte',  'Distrito Demo B', 9.878000, -83.905000),
 ('DEMO-Z003', 'Zona demostrativa Sur',    'Distrito Demo C', 9.850000, -83.925000),
 ('DEMO-Z004', 'Zona demostrativa Este',   'Distrito Demo D', 9.859000, -83.890000),
 ('DEMO-Z005', 'Zona demostrativa Oeste',  'Distrito Demo E', 9.867000, -83.940000)
ON CONFLICT (id_ubicacion) DO NOTHING;

INSERT INTO public.categoria_sensor (id_categoria, nombre_categoria) VALUES
 (900001, 'DEMO - Calidad del aire'),
 (900002, 'DEMO - Meteorologia')
ON CONFLICT DO NOTHING;

INSERT INTO public.tipo_sensor (tipo_sensor, id_categoria) VALUES
 ('demo_particulas', 900001),
 ('demo_gases', 900001),
 ('demo_termometro', 900002)
ON CONFLICT (tipo_sensor) DO NOTHING;

INSERT INTO public.organismo_responsable (id_organismo, nombre, responsable) VALUES
 (900001, 'DEMO - Unidad Ambiental', NULL),
 (900002, 'DEMO - Laboratorio Urbano', 'Contacto de prueba'),
 (900003, 'DEMO - Centro de Monitoreo', NULL)
ON CONFLICT (id_organismo) DO NOTHING;

INSERT INTO public.usuario (id_usuario, nombre, apellido1, apellido2, correo) VALUES
 (900001, 'Ana', 'Mora', NULL, 'ana.demo@ejemplo.invalid'),
 (900002, 'Luis', 'Vargas', 'Rojas', 'luis.demo@ejemplo.invalid'),
 (900003, 'Marta', 'Solano', NULL, 'marta.demo@ejemplo.invalid'),
 (900004, 'Carlos', 'Soto', 'Arias', 'carlos.demo@ejemplo.invalid'),
 (900005, 'Sofia', 'Jimenez', 'Castro', 'sofia.demo@ejemplo.invalid')
ON CONFLICT DO NOTHING;

INSERT INTO public.variable_medicion (id_variable, nombre_variable, unidad_canonica) VALUES
 (900001, 'demo_pm25', 'µg/m³'),
 (900002, 'demo_pm10', 'µg/m³'),
 (900003, 'demo_temperatura', '°C')
ON CONFLICT DO NOTHING;

INSERT INTO public.sensor
 (id_sensor, nombre, tipo_sensor, fecha_instalacion, estado, id_ubicacion, id_organismo)
VALUES
 ('DEMO-S001','Sensor sintético PM2.5 Centro',  'demo_particulas', '2024-02-10','activo',   'DEMO-Z001',900001),
 ('DEMO-S002','Sensor sintético PM10 Centro',   'demo_particulas', '2024-02-11','activo',   'DEMO-Z001',900001),
 ('DEMO-S003','Sensor sintético PM2.5 Norte',   'demo_particulas', '2024-03-10','activo',   'DEMO-Z002',900001),
 ('DEMO-S004','Sensor sintético PM10 Sur',      'demo_particulas', '2024-04-10','inactivo', 'DEMO-Z003',900002),
 ('DEMO-S005','Sensor sintético PM2.5 Este',    'demo_particulas', NULL,        'activo',   'DEMO-Z004',900002),
 ('DEMO-S006','Sensor sintético temperatura N', 'demo_termometro','2023-11-21','activo',   'DEMO-Z002',900003),
 ('DEMO-S007','Sensor sintético temperatura O', 'demo_termometro','2023-12-01','inactivo', 'DEMO-Z005',900003),
 ('DEMO-S008','Sensor sintético temperatura S', 'demo_termometro',NULL,        'activo',   'DEMO-Z003',900003),
 ('DEMO-S009','Sensor sintético sin lecturas',  'demo_gases',      NULL,        'inactivo', 'DEMO-Z005',900001),
 ('DEMO-S010','Sensor sintético sin lecturas 2','demo_particulas', NULL,        'activo',   'DEMO-Z004',900002)
ON CONFLICT (id_sensor) DO NOTHING;

-- 100 mediciones deterministas, distribuidas entre ocho sensores.
-- El numero n selecciona el sensor; el tiempo usa intervalos horarios en UTC.
WITH asignaciones (posicion, id_sensor, id_variable, base) AS (
 VALUES
 (0,'DEMO-S001',900001,12.0::numeric),
 (1,'DEMO-S002',900002,19.0::numeric),
 (2,'DEMO-S003',900001,15.0::numeric),
 (3,'DEMO-S004',900002,21.0::numeric),
 (4,'DEMO-S005',900001,11.0::numeric),
 (5,'DEMO-S006',900003,23.0::numeric),
 (6,'DEMO-S007',900003,20.0::numeric),
 (7,'DEMO-S008',900003,24.0::numeric)
)
INSERT INTO public.medicion (id_medicion, id_sensor, id_variable, fecha_utc, valor, fuente)
SELECT 9000001 + n,
       a.id_sensor,
       a.id_variable,
       TIMESTAMPTZ '2025-01-01 00:00:00+00' + ((n / 8) * INTERVAL '1 hour'),
       a.base + ((n % 7)::numeric * 0.5),
       'DEMO - generado por 02_seed.sql'
FROM generate_series(0,99) AS serie(n)
JOIN asignaciones a ON a.posicion = (n % 8)
ON CONFLICT (id_medicion) DO NOTHING;

-- Validacion minima de esta muestra (cuenta solamente IDs DEMO/reservados).
DO $$
DECLARE
    cantidad_sensores integer;
    cantidad_mediciones integer;
    sensores_sin_lecturas integer;
BEGIN
    SELECT count(*) INTO cantidad_sensores
    FROM public.sensor WHERE id_sensor LIKE 'DEMO-S%';
    SELECT count(*) INTO cantidad_mediciones
    FROM public.medicion WHERE id_medicion BETWEEN 9000001 AND 9000100;
    SELECT count(*) INTO sensores_sin_lecturas
    FROM public.sensor s
    WHERE s.id_sensor IN ('DEMO-S009','DEMO-S010')
      AND NOT EXISTS (SELECT 1 FROM public.medicion m WHERE m.id_sensor = s.id_sensor);

    IF cantidad_sensores < 10 OR cantidad_mediciones <> 100 OR sensores_sin_lecturas <> 2 THEN
        RAISE EXCEPTION 'Muestra incompleta: sensores %, mediciones %, sin lecturas %',
            cantidad_sensores, cantidad_mediciones, sensores_sin_lecturas;
    END IF;
    RAISE NOTICE 'OK: 10 sensores DEMO, 100 mediciones DEMO y 2 sensores sin mediciones';
END $$;

COMMIT;
