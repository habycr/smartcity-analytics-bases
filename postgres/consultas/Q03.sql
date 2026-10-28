-- Q03 | Cantidad de sensores activos e inactivos.
-- Se muestran ambos estados incluso si alguno tiene cero sensores.
SELECT estados.estado, COUNT(s.id_sensor) AS cantidad_sensores
FROM (VALUES ('activo'), ('inactivo')) AS estados(estado)
LEFT JOIN public.sensor AS s ON s.estado = estados.estado
GROUP BY estados.estado
ORDER BY estados.estado;
