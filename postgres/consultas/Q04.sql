-- Q04 | Numero de sensores por organismo responsable.
-- DISTINCT evita contar el mismo id_sensor mas de una vez.
-- LEFT JOIN conserva organismos que aun no tengan sensores.
SELECT o.id_organismo, o.nombre AS organismo,
       COUNT(DISTINCT s.id_sensor) AS cantidad_sensores
FROM public.organismo_responsable AS o
LEFT JOIN public.sensor AS s ON s.id_organismo = o.id_organismo
GROUP BY o.id_organismo, o.nombre
ORDER BY cantidad_sensores DESC, o.nombre, o.id_organismo;
