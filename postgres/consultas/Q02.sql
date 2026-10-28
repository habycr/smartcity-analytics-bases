-- Q02 | Sensores por ubicación.
SELECT u.id_ubicacion, u.nombre_zona, u.distrito,
       s.id_sensor, s.nombre AS nombre_sensor, s.tipo_sensor, s.estado
FROM public.ubicacion AS u
JOIN public.sensor AS s ON s.id_ubicacion = u.id_ubicacion
ORDER BY u.nombre_zona, u.id_ubicacion, s.id_sensor;
