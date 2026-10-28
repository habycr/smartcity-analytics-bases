-- Q08 | Ranking de zonas monitoreadas por número de sensores.
-- Zona = id_ubicacion (estación). DENSE_RANK mantiene empates.
WITH cobertura AS (
    SELECT u.id_ubicacion, u.nombre_zona, u.distrito,
           COUNT(s.id_sensor) AS cantidad_sensores
    FROM public.ubicacion AS u
    LEFT JOIN public.sensor AS s ON s.id_ubicacion = u.id_ubicacion
    GROUP BY u.id_ubicacion, u.nombre_zona, u.distrito
)
SELECT DENSE_RANK() OVER (ORDER BY cantidad_sensores DESC) AS posicion,
       id_ubicacion, nombre_zona, distrito, cantidad_sensores
FROM cobertura
ORDER BY posicion, id_ubicacion
LIMIT 20;
