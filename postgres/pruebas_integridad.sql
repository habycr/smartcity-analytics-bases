-- SmartCity Analytics | PostgreSQL 16 | Pruebas de integridad
-- EJECUTAR SOLO EN BASE DE PRUEBAS CON 01_schema.sql YA APLICADO.
-- Ejecutar con psql -v ON_ERROR_STOP=1 -f postgres/pruebas_integridad.sql
-- Todos los cambios se revierten con ROLLBACK, incluso cuando hay pruebas válidas.
-- SQLSTATE: 23505 UNIQUE, 23503 FK, 23514 CHECK, 23502 NOT NULL.
\set ON_ERROR_STOP on
BEGIN;

CREATE TEMP TABLE prueba_resultado (
    numero INTEGER GENERATED ALWAYS AS IDENTITY,
    descripcion TEXT NOT NULL,
    resultado TEXT NOT NULL,
    CONSTRAINT prueba_resultado_estado CHECK (resultado = 'OK')
) ON COMMIT DROP;

CREATE FUNCTION pg_temp.esperar_error(
    descripcion TEXT, sentencia TEXT, codigo_esperado TEXT
) RETURNS void LANGUAGE plpgsql AS $func$
DECLARE
    codigo_obtenido TEXT;
BEGIN
    BEGIN
        EXECUTE sentencia;
    EXCEPTION WHEN OTHERS THEN
        GET STACKED DIAGNOSTICS codigo_obtenido = RETURNED_SQLSTATE;
        IF codigo_obtenido <> codigo_esperado THEN
            RAISE EXCEPTION 'FALLÓ [%]: se esperaba SQLSTATE %, se obtuvo %',
                descripcion, codigo_esperado, codigo_obtenido;
        END IF;
        INSERT INTO pg_temp.prueba_resultado(descripcion, resultado)
        VALUES (descripcion, 'OK');
        RETURN;
    END;
    RAISE EXCEPTION 'FALLÓ [%]: la operación inválida fue aceptada (esperado SQLSTATE %)',
        descripcion, codigo_esperado;
END;
$func$;

-- Datos válidos mínimos de prueba; IDs reservados con prefijo TST-.
INSERT INTO public.ubicacion (id_ubicacion, nombre_zona, distrito, latitud, longitud)
VALUES ('TST-ZONA-1', 'Zona de prueba', 'Distrito de prueba', 9.930000, -84.090000);
INSERT INTO public.categoria_sensor (id_categoria, nombre_categoria)
VALUES (-900001, 'TST-CATEGORIA');
INSERT INTO public.tipo_sensor (tipo_sensor, id_categoria)
VALUES ('TST-PARTICULAS', -900001);
INSERT INTO public.organismo_responsable (id_organismo, nombre, responsable)
VALUES (-900001, 'TST-ORGANISMO', NULL);
INSERT INTO public.variable_medicion (id_variable, nombre_variable, unidad_canonica)
VALUES (-900001, 'TST-PM25', 'µg/m³');
INSERT INTO public.usuario (id_usuario, nombre, apellido1, apellido2, correo)
VALUES (-900001, 'Nombre Prueba', 'Apellido', NULL, 'Prueba@Ejemplo.com');
INSERT INTO public.sensor
    (id_sensor, nombre, tipo_sensor, fecha_instalacion, estado, id_ubicacion, id_organismo)
VALUES ('TST-SENSOR-1', 'Sensor de prueba', 'TST-PARTICULAS', NULL,
        'activo', 'TST-ZONA-1', -900001);
INSERT INTO public.medicion
    (id_medicion, id_sensor, id_variable, fecha_utc, valor, fuente)
VALUES (-900001, 'TST-SENSOR-1', -900001,
        '2025-01-01 12:00:00+00', -0.125000, 'TST-EPA');

-- Prueba positiva: relaciones válidas, NULL opcionales y valor negativo permitido.
DO $validas$
BEGIN
    IF (SELECT COUNT(*) FROM public.medicion
        WHERE id_medicion = -900001 AND valor = -0.125000) <> 1
       OR (SELECT COUNT(*) FROM public.usuario
           WHERE id_usuario = -900001 AND apellido2 IS NULL
             AND correo = 'Prueba@Ejemplo.com') <> 1
       OR (SELECT COUNT(*) FROM public.sensor
           WHERE id_sensor = 'TST-SENSOR-1' AND fecha_instalacion IS NULL) <> 1
       OR (SELECT COUNT(*) FROM public.organismo_responsable
           WHERE id_organismo = -900001 AND responsable IS NULL) <> 1 THEN
        RAISE EXCEPTION 'FALLÓ: inserciones válidas, valores opcionales o correo original';
    END IF;
    INSERT INTO pg_temp.prueba_resultado (descripcion, resultado)
    VALUES ('Inserciones válidas, NULL opcionales, correo conservado y medición negativa', 'OK');
END;
$validas$;

-- Pruebas negativas: deben fallar con la restricción correspondiente.
SELECT pg_temp.esperar_error('PK duplicada de ubicación',
    $q$INSERT INTO public.ubicacion VALUES ('TST-ZONA-1','Otra','Distrito',10,-84)$q$, '23505');
SELECT pg_temp.esperar_error('Latitud fuera de rango',
    $q$INSERT INTO public.ubicacion VALUES ('TST-ZONA-LAT','Fuera','Distrito',91,-84)$q$, '23514');
SELECT pg_temp.esperar_error('Longitud fuera de rango',
    $q$INSERT INTO public.ubicacion VALUES ('TST-ZONA-LON','Fuera','Distrito',10,-181)$q$, '23514');
SELECT pg_temp.esperar_error('Ubicación sin nombre',
    $q$INSERT INTO public.ubicacion VALUES ('TST-ZONA-NULL',NULL,'Distrito',10,-84)$q$, '23502');
SELECT pg_temp.esperar_error('Categoría duplicada',
    $q$INSERT INTO public.categoria_sensor (id_categoria,nombre_categoria) VALUES (-900002,'TST-CATEGORIA')$q$, '23505');
SELECT pg_temp.esperar_error('Tipo de sensor con categoría inexistente',
    $q$INSERT INTO public.tipo_sensor VALUES ('TST-TIPO-INVALIDO', -900002)$q$, '23503');
SELECT pg_temp.esperar_error('Variable duplicada',
    $q$INSERT INTO public.variable_medicion VALUES (-900002,'TST-PM25','µg/m³')$q$, '23505');
SELECT pg_temp.esperar_error('Correo duplicado exacto',
    $q$INSERT INTO public.usuario VALUES (-900002,'Otro','Apellido',NULL,'Prueba@Ejemplo.com')$q$, '23505');
SELECT pg_temp.esperar_error('Sensor con estado no permitido',
    $q$INSERT INTO public.sensor VALUES ('TST-SENSOR-2','Incorrecto','TST-PARTICULAS',NULL,'mantenimiento','TST-ZONA-1',-900001)$q$, '23514');
SELECT pg_temp.esperar_error('Sensor con ubicación inexistente',
    $q$INSERT INTO public.sensor VALUES ('TST-SENSOR-2','Incorrecto','TST-PARTICULAS',NULL,'activo','TST-NO-EXISTE',-900001)$q$, '23503');
SELECT pg_temp.esperar_error('Sensor con organismo inexistente',
    $q$INSERT INTO public.sensor VALUES ('TST-SENSOR-2','Incorrecto','TST-PARTICULAS',NULL,'activo','TST-ZONA-1',-900002)$q$, '23503');
SELECT pg_temp.esperar_error('Sensor sin tipo de sensor',
    $q$INSERT INTO public.sensor VALUES ('TST-SENSOR-2','Incorrecto',NULL,NULL,'activo','TST-ZONA-1',-900001)$q$, '23502');
SELECT pg_temp.esperar_error('Medición con sensor inexistente',
    $q$INSERT INTO public.medicion VALUES (-900002,'TST-NO-EXISTE',-900001,'2025-01-01 12:00:00+00',1,'TST-EPA')$q$, '23503');
SELECT pg_temp.esperar_error('Medición con variable inexistente',
    $q$INSERT INTO public.medicion VALUES (-900002,'TST-SENSOR-1',-900002,'2025-01-01 12:00:00+00',1,'TST-EPA')$q$, '23503');
SELECT pg_temp.esperar_error('Medición sin fecha',
    $q$INSERT INTO public.medicion VALUES (-900002,'TST-SENSOR-1',-900001,NULL,1,'TST-EPA')$q$, '23502');
SELECT pg_temp.esperar_error('No eliminar ubicación referenciada (RESTRICT)',
    $q$DELETE FROM public.ubicacion WHERE id_ubicacion = 'TST-ZONA-1'$q$, '23503');
SELECT pg_temp.esperar_error('No eliminar sensor con mediciones (RESTRICT)',
    $q$DELETE FROM public.sensor WHERE id_sensor = 'TST-SENSOR-1'$q$, '23503');

-- Resumen antes de revertir.
SELECT numero, descripcion, resultado FROM pg_temp.prueba_resultado ORDER BY numero;
DO $resumen$
DECLARE total INT;
BEGIN
    SELECT COUNT(*) INTO total FROM pg_temp.prueba_resultado;
    IF total <> 18 THEN
        RAISE EXCEPTION 'Cantidad de pruebas incorrecta: %; se esperaban 18', total;
    END IF;
    RAISE NOTICE 'OK: % pruebas de integridad superadas; se revertirán los datos', total;
END;
$resumen$;

ROLLBACK;
-- La tabla temporal y la función temporal desaparecen al revertir la transacción.
