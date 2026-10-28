-- Q07 | Sensores sin actividad registrada (nunca reportaron).
-- NOT EXISTS evita multiplicaciones de filas y distingue ausencia total de lecturas.
SELECT s.id_sensor, s.nombre AS nombre_sensor, s.tipo_sensor,
       s.estado, u.nombre_zona, u.id_ubicacion
FROM public.sensor AS s
JOIN public.ubicacion AS u ON u.id_ubicacion = s.id_ubicacion
WHERE NOT EXISTS (
    SELECT 1 FROM public.medicion AS m WHERE m.id_sensor = s.id_sensor
)
ORDER BY s.id_sensor;
