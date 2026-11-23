"""S01: sensores que generan más información, medida en lecturas."""

from datetime import datetime, timezone

from pyspark.sql import DataFrame, functions as F

from spark.contrato import validar_lecturas


def instante_utc(valor: str | datetime | None) -> datetime | None:
    """Exige zona explícita; normaliza offsets sin depender de la zona del host."""
    if valor is None:
        return None
    if isinstance(valor, str):
        valor = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    if not isinstance(valor, datetime) or valor.tzinfo is None or valor.utcoffset() is None:
        raise ValueError("La fecha debe ser un instante ISO 8601 con zona explícita")
    return valor.astimezone(timezone.utc)


def sensores_mas_informacion(
    lecturas: DataFrame,
    *,
    desde: str | datetime | None = None,
    hasta: str | datetime | None = None,
    zona_id: str | None = None,
    sintetico: bool | None = None,
) -> DataFrame:
    """Cuenta filas por sensor; ordena cantidad DESC, sensor_id ASC.

    Fechas [desde, hasta), zona exacta y sintetico se combinan con AND.
    None omite ese filtro. Duplicados cuentan como filas independientes.
    La validación de entrada es inmediata; el agregado retornado es perezoso.
    """
    desde, hasta = instante_utc(desde), instante_utc(hasta)
    if desde is not None and hasta is not None and desde >= hasta:
        raise ValueError("desde debe ser anterior a hasta")
    if zona_id is not None and (not isinstance(zona_id, str) or not zona_id.strip()):
        raise ValueError("zona_id debe ser una cadena no vacía")
    if sintetico is not None and type(sintetico) is not bool:
        raise ValueError("sintetico debe ser bool o None")
    validar_lecturas(lecturas)
    seleccion = lecturas
    if desde is not None:
        seleccion = seleccion.where(F.col("fecha_utc") >= F.lit(desde))
    if hasta is not None:
        seleccion = seleccion.where(F.col("fecha_utc") < F.lit(hasta))
    if zona_id is not None:
        seleccion = seleccion.where(F.col("zona_id") == zona_id)
    if sintetico is not None:
        seleccion = seleccion.where(F.col("sintetico") == F.lit(sintetico))
    return (
        seleccion.groupBy("sensor_id")
        .agg(F.count(F.lit(1)).alias("cantidad_lecturas"))
        .orderBy(F.desc("cantidad_lecturas"), F.asc("sensor_id"))
    )
