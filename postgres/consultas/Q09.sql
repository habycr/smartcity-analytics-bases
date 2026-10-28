-- Q09 | Consulta utilizando una vista.
-- La vista TEMPORAL existe solo durante esta conexion a PostgreSQL.
-- SUM cuenta sensores por estado; AVG calcula sensores por ubicacion en todas las zonas.
CREATE OR REPLACE TEMP VIEW vw_resumen_sensores_ubicacion AS
SELECT u.id_ubicacion, u.nombre_zona, u.distrito,
       COUNT(s.id_sensor) AS cantidad_sensores,
       SUM(CASE WHEN s.estado = 'activo' THEN 1 ELSE 0 END)::bigint AS sensores_activos,
       SUM(CASE WHEN s.estado = 'inactivo' THEN 1 ELSE 0 END)::bigint AS sensores_inactivos
FROM public.ubicacion AS u
LEFT JOIN public.sensor AS s ON s.id_ubicacion = u.id_ubicacion
GROUP BY u.id_ubicacion, u.nombre_zona, u.distrito;

SELECT id_ubicacion, nombre_zona, distrito,
       cantidad_sensores, sensores_activos, sensores_inactivos,
       ROUND(AVG(cantidad_sensores) OVER (), 2) AS promedio_sensores_por_ubicacion
FROM vw_resumen_sensores_ubicacion
ORDER BY cantidad_sensores DESC, id_ubicacion
LIMIT 20;
