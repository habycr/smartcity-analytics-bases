"""Propuesta de entrada curated v1; véase spark/README.md."""

from functools import reduce
from operator import or_

from pyspark.sql import DataFrame, functions as F, types as T


ESQUEMA_LECTURAS = T.StructType([
    T.StructField(nombre, tipo, True)
    for nombre, tipo in [
        ("lectura_id", T.StringType()),
        ("sensor_id", T.StringType()),
        ("zona_id", T.StringType()),
        ("tipo_sensor", T.StringType()),
        ("variable", T.StringType()),
        ("valor", T.DecimalType(18, 6)),
        ("unidad", T.StringType()),
        ("fecha_utc", T.TimestampType()),
        ("fuente", T.StringType()),
        ("sintetico", T.BooleanType()),
    ]
])


def exigir_utc(df: DataFrame) -> None:
    if df.sparkSession.conf.get("spark.sql.session.timeZone") != "UTC":
        raise ValueError("Se requiere spark.sql.session.timeZone=UTC")


def validar_lecturas(df: DataFrame) -> None:
    """Valida toda la entrada antes de filtrar; ejecuta una acción Spark.

    No recoge filas en Python, no repara nulos ni elimina duplicados.
    nullable=True permite inspeccionar y rechazar nulos con un error explícito.
    """
    exigir_utc(df)
    if len(df.columns) != len(set(df.columns)):
        raise ValueError("Columnas repetidas en el DataFrame")
    tipos = {campo.name: campo.dataType for campo in df.schema}
    for campo in ESQUEMA_LECTURAS:
        if campo.name not in tipos:
            raise ValueError(f"Falta columna requerida: {campo.name}")
        if tipos[campo.name] != campo.dataType:
            raise ValueError(f"Tipo incorrecto para {campo.name}: se requiere {campo.dataType}")
    invalidos = [F.col(c.name).isNull() for c in ESQUEMA_LECTURAS]
    invalidos.extend(
        F.length(F.trim(F.col(c.name))) == 0
        for c in ESQUEMA_LECTURAS if isinstance(c.dataType, T.StringType)
    )
    if df.where(reduce(or_, invalidos)).limit(1).count():
        raise ValueError("Entrada inválida: nulos o cadenas vacías en columnas requeridas")
