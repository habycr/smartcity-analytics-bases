-- Q05 | Ubicaciones con mayor cantidad de sensores.
-- HAVING excluye ubicaciones sin sensores del ranking de mayor cobertura.
SELECT u.id_ubicacion, u.nombre_zona, u.distrito,
       COUNT(s.id_sensor) AS cantidad_sensores
FROM public.ubicacion AS u
LEFT JOIN public.sensor AS s ON s.id_ubicacion = u.id_ubicacion
GROUP BY u.id_ubicacion, u.nombre_zona, u.distrito
HAVING COUNT(s.id_sensor) > 0
ORDER BY cantidad_sensores DESC, u.id_ubicacion
LIMIT 20;
