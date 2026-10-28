-- SmartCity Analytics | Fabio | Indice de optimizacion PostgreSQL
-- Ejecutar SOLO en una base autorizada. En Azure ya se creo manualmente.
-- Idempotente para evitar fallar al repetir un despliegue.
-- Uso previsto: filtros por id_sensor y rangos de fecha_utc.
CREATE INDEX IF NOT EXISTS idx_medicion_sensor_fecha
    ON public.medicion USING btree (id_sensor, fecha_utc);
