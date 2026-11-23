"""Ejecutar desde la raíz: python -m spark.cli --help."""

import argparse

from pyspark.sql import SparkSession

from spark.consultas.S01 import sensores_mas_informacion
from spark.entrada import leer_lecturas


def main() -> None:
    parser = argparse.ArgumentParser(description="S01: cantidad de lecturas por sensor")
    parser.add_argument("--entrada", required=True)
    parser.add_argument("--formato", choices=("jsonl", "parquet"), required=True)
    parser.add_argument("--desde")
    parser.add_argument("--hasta")
    parser.add_argument("--zona-id")
    parser.add_argument("--datos", choices=("todos", "reales", "sinteticos"), default="todos")
    parser.add_argument("--master", default="local[2]")
    parser.add_argument("--limite", type=int, default=20, help="Filas mostradas, no limita el análisis")
    args = parser.parse_args()
    if args.limite < 1:
        parser.error("--limite debe ser positivo")
    sesion = (SparkSession.builder.appName("SmartCity-S01").master(args.master)
              .config("spark.sql.session.timeZone", "UTC")
              .config("spark.sql.timestampType", "TIMESTAMP_LTZ")
              .config("spark.sql.ansi.enabled", "true")
              .getOrCreate())
    try:
        resultado = sensores_mas_informacion(
            leer_lecturas(sesion, args.entrada, args.formato),
            desde=args.desde, hasta=args.hasta, zona_id=args.zona_id,
            sintetico={"todos": None, "reales": False, "sinteticos": True}[args.datos],
        )
        resultado.show(args.limite, truncate=False)
    finally:
        sesion.stop()


if __name__ == "__main__":
    main()
