-- Q10 | Consulta mediante una funcion almacenada.
-- Funcion TEMPORAL (pg_temp): no modifica el esquema permanente en Azure.
-- Fechas UTC en intervalo semiabierto: desde inclusivo, hasta exclusivo.
CREATE OR REPLACE FUNCTION pg_temp.fn_actividad_sensores(
    p_id_ubicacion varchar,
    p_desde timestamptz,
    p_hasta timestamptz
)
RETURNS TABLE (
    id_sensor varchar,
    nombre_sensor varchar,
    id_ubicacion varchar,
    cantidad_mediciones bigint,
    primera_medicion timestamptz,
    ultima_medicion timestamptz
)
LANGUAGE sql STABLE AS $$
    SELECT s.id_sensor, s.nombre, s.id_ubicacion,
           COUNT(m.id_medicion), MIN(m.fecha_utc), MAX(m.fecha_utc)
    FROM public.sensor AS s
    LEFT JOIN public.medicion AS m
      ON m.id_sensor = s.id_sensor
     AND m.fecha_utc >= p_desde
     AND m.fecha_utc < p_hasta
    WHERE (p_id_ubicacion IS NULL OR s.id_ubicacion = p_id_ubicacion)
      AND p_desde IS NOT NULL AND p_hasta IS NOT NULL AND p_desde < p_hasta
    GROUP BY s.id_sensor, s.nombre, s.id_ubicacion
$$;

SELECT *
FROM pg_temp.fn_actividad_sensores(
    NULL::varchar,
    '2025-01-01 00:00:00+00'::timestamptz,
    '2026-01-01 00:00:00+00'::timestamptz
)
ORDER BY cantidad_mediciones DESC, id_sensor
LIMIT 20;
