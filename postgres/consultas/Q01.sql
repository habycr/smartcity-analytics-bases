-- Q01 | Sensores por tipo.
-- Muestra todos los tipos; se puede añadir WHERE s.tipo_sensor = 'particulas'.
SELECT s.tipo_sensor, c.nombre_categoria, s.id_sensor,
       s.nombre AS nombre_sensor, s.estado
FROM public.sensor AS s
JOIN public.tipo_sensor AS t ON t.tipo_sensor = s.tipo_sensor
JOIN public.categoria_sensor AS c ON c.id_categoria = t.id_categoria
ORDER BY s.tipo_sensor, s.nombre, s.id_sensor;
