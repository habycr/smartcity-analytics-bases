"""Lectura de la propuesta curated: Parquet tipado o JSONL normalizado."""

from pyspark.sql import DataFrame, SparkSession, functions as F, types as T

from spark.contrato import ESQUEMA_LECTURAS, exigir_utc


def leer_lecturas(sesion: SparkSession, ruta: str, formato: str) -> DataFrame:
    """No interpreta BSON/Extended JSON ni implementa el ETL de fuentes crudas.

    S01 comprueba después esquema y nulos del DataFrame tipado.
    """
    if formato == "parquet":
        return sesion.read.parquet(ruta)
    if formato != "jsonl":
        raise ValueError("Formato permitido: jsonl o parquet")
    esquema_texto = T.StructType([
        T.StructField(c.name, T.StringType() if c.name in ("valor", "fecha_utc")
                      else c.dataType, True)
        for c in ESQUEMA_LECTURAS
    ])
    crudo = sesion.read.schema(esquema_texto).option("mode", "FAILFAST").json(ruta)
    exigir_utc(crudo)
    # Comprobar la representación ANTES del cast evita redondeo silencioso.
    decimal_valido = F.col("valor").rlike(r"^-?(0|[1-9][0-9]{0,11})(\.[0-9]{1,6})?$")
    fecha_valida = F.col("fecha_utc").rlike(
        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$"
    )
    if crudo.where(~decimal_valido | ~fecha_valida).limit(1).count():
        raise ValueError("JSONL requiere valor decimal(18,6) sin redondeo y fecha_utc ISO UTC con Z")
    return crudo.withColumn("valor", F.col("valor").cast(T.DecimalType(18, 6))).withColumn(
        "fecha_utc", F.try_to_timestamp("fecha_utc", F.lit("yyyy-MM-dd'T'HH:mm:ss[.SSSSSS]X"))
    )
