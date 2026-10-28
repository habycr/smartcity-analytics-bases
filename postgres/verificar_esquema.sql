-- Comprobación de estructura de PostgreSQL 16; lectura sin efectos secundarios.
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
  AND table_name IN ('ubicacion', 'categoria_sensor', 'tipo_sensor',
                     'organismo_responsable', 'usuario', 'sensor',
                     'variable_medicion', 'medicion')
ORDER BY table_name;

SELECT tc.table_name, tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public'
  AND tc.table_name IN ('ubicacion', 'categoria_sensor', 'tipo_sensor',
                        'organismo_responsable', 'usuario', 'sensor',
                        'variable_medicion', 'medicion')
ORDER BY tc.table_name, tc.constraint_type, tc.constraint_name;

SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND
      (table_name, column_name) IN
      (('sensor', 'fecha_instalacion'), ('sensor', 'estado'),
       ('organismo_responsable', 'responsable'), ('usuario', 'apellido2'))
ORDER BY table_name, column_name;

-- Controles automáticos: lanzan error si faltan tablas, PK o FK.
DO $test$
DECLARE
    n_tablas INT;
    n_pk INT;
    n_fk INT;
BEGIN
    SELECT COUNT(*) INTO n_tablas
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
      AND table_name IN ('ubicacion', 'categoria_sensor', 'tipo_sensor',
                         'organismo_responsable', 'usuario', 'sensor',
                         'variable_medicion', 'medicion');

    SELECT COUNT(*) INTO n_pk
    FROM information_schema.table_constraints
    WHERE table_schema = 'public' AND constraint_type = 'PRIMARY KEY'
      AND table_name IN ('ubicacion', 'categoria_sensor', 'tipo_sensor',
                         'organismo_responsable', 'usuario', 'sensor',
                         'variable_medicion', 'medicion');

    SELECT COUNT(*) INTO n_fk
    FROM information_schema.table_constraints
    WHERE table_schema = 'public' AND constraint_type = 'FOREIGN KEY'
      AND table_name IN ('ubicacion', 'categoria_sensor', 'tipo_sensor',
                         'organismo_responsable', 'usuario', 'sensor',
                         'variable_medicion', 'medicion');

    IF n_tablas <> 8 OR n_pk <> 8 OR n_fk <> 6 THEN
        RAISE EXCEPTION 'Esquema incompleto: tablas=%, PK=%, FK=% (esperado 8/8/6)',
            n_tablas, n_pk, n_fk;
    END IF;
    RAISE NOTICE 'OK: % tablas, % PK, % FK', n_tablas, n_pk, n_fk;
END;
$test$;
