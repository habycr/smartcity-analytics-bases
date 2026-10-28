-- Q06 | Sensores instalados por año.
-- EPA no acredita fecha física de instalación; el informe excluye los NULL.
-- 'Sin fecha acreditada' NO equivale a un año real de instalación.
SELECT EXTRACT(YEAR FROM fecha_instalacion)::int AS anio_instalacion,
       COUNT(*) AS cantidad_sensores
FROM public.sensor
WHERE fecha_instalacion IS NOT NULL
GROUP BY EXTRACT(YEAR FROM fecha_instalacion)
ORDER BY anio_instalacion;
-- Comprobación complementaria sobre la ausencia de fechas.
SELECT COUNT(*) AS sensores_sin_fecha_instalacion
FROM public.sensor
WHERE fecha_instalacion IS NULL;
