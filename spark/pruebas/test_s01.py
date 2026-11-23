"""Pruebas locales con Spark real y entradas pequeñas, sin servicios externos."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from pyspark.sql import SparkSession, functions as F, types as T

from spark.contrato import ESQUEMA_LECTURAS
from spark.consultas.S01 import sensores_mas_informacion as s01
from spark.entrada import leer_lecturas


MUESTRA = Path(__file__).resolve().parents[1] / "datos_muestra/lecturas_sinteticas.jsonl"
DIA = {"desde": "2025-01-01T00:00:00Z", "hasta": "2025-01-02T00:00:00Z"}


class S01Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sesion = (SparkSession.builder.master("local[2]").appName("pruebas-S01")
                      .config("spark.ui.enabled", "false")
                      .config("spark.sql.shuffle.partitions", "2")
                      .config("spark.sql.session.timeZone", "UTC")
                      .config("spark.sql.timestampType", "TIMESTAMP_LTZ")
                      .config("spark.sql.ansi.enabled", "true").getOrCreate())
        cls.sesion.sparkContext.setLogLevel("ERROR")
        cls.df = leer_lecturas(cls.sesion, str(MUESTRA), "jsonl").cache()
        cls.df.count()

    @classmethod
    def tearDownClass(cls):
        cls.df.unpersist()
        cls.sesion.stop()

    def resultado(self, df=None, **filtros):
        # collect exclusivamente de resultados de esta muestra de ocho filas.
        return [tuple(r) for r in s01(self.df if df is None else df, **filtros).collect()]

    def test_conteos_y_empates_entre_particiones(self):
        for particiones in (1, 3):
            with self.subTest(particiones=particiones):
                resultado = s01(self.df.repartition(particiones))
                self.assertEqual(resultado.schema["cantidad_lecturas"].dataType, T.LongType())
                self.assertEqual([tuple(r) for r in resultado.collect()],
                                 [("DEMO-SA", 3), ("DEMO-SB", 3), ("DEMO-SC", 2)])

    def test_limites_inicio_incluido_fin_excluido_microsegundos(self):
        self.assertEqual(self.resultado(**DIA), [("DEMO-SA", 2), ("DEMO-SB", 2), ("DEMO-SC", 1)])

    def test_limites_independientes(self):
        self.assertEqual(self.resultado(desde=DIA["hasta"]), [("DEMO-SA", 1), ("DEMO-SC", 1)])
        self.assertEqual(self.resultado(hasta=DIA["desde"]), [("DEMO-SB", 1)])

    def test_offsets_equivalentes_a_utc(self):
        self.assertEqual(self.resultado(desde="2024-12-31T18:00:00-06:00",
                                        hasta="2025-01-01T18:00:00-06:00"), self.resultado(**DIA))

    def test_zona_y_filtros_combinados(self):
        self.assertEqual(self.resultado(zona_id="DEMO-Z1"), [("DEMO-SA", 3), ("DEMO-SC", 2)])
        self.assertEqual(self.resultado(zona_id="DEMO-Z1", sintetico=True, **DIA),
                         [("DEMO-SA", 2), ("DEMO-SC", 1)])
        self.assertEqual(self.resultado(zona_id="NO-EXISTE"), [])

    def test_reales_sinteticos_y_todos(self):
        self.assertEqual(self.resultado(sintetico=False), [])
        self.assertEqual(self.resultado(sintetico=True), self.resultado())
        # Modificar solo etiquetas en memoria prueba ambas ramas; NO crea datos reales.
        mixto = self.df.withColumn("sintetico", F.col("sensor_id") != "DEMO-SB")
        self.assertEqual(self.resultado(mixto, sintetico=False), [("DEMO-SB", 3)])
        self.assertEqual(self.resultado(mixto, sintetico=True), [("DEMO-SA", 3), ("DEMO-SC", 2)])

    def test_vacio_y_periodo_sin_lecturas(self):
        vacio = self.sesion.createDataFrame([], ESQUEMA_LECTURAS)
        self.assertEqual(self.resultado(vacio), [])
        self.assertEqual(s01(vacio).columns, ["sensor_id", "cantidad_lecturas"])
        self.assertEqual(self.resultado(desde="2030-01-01T00:00:00Z"), [])

    def test_duplicados_se_cuentan_sin_deduplicar(self):
        duplicado = self.df.where(F.col("lectura_id") == "muestra:DEMO-L004")
        self.assertEqual(self.resultado(self.df.unionByName(duplicado)),
                         [("DEMO-SB", 4), ("DEMO-SA", 3), ("DEMO-SC", 2)])

    def test_todas_las_columnas_requeridas(self):
        for campo in ESQUEMA_LECTURAS:
            with self.subTest(campo=campo.name), self.assertRaisesRegex(ValueError, "Falta columna"):
                s01(self.df.drop(campo.name))

    def test_tipos_incorrectos_no_se_convierten(self):
        for campo, tipo in (("sensor_id", "int"), ("fecha_utc", "string"),
                            ("valor", "double"), ("sintetico", "string")):
            with self.subTest(campo=campo), self.assertRaisesRegex(ValueError, "Tipo incorrecto"):
                s01(self.df.withColumn(campo, F.lit(None).cast(tipo)))

    def test_nulos_rechazados_incluso_fuera_del_filtro(self):
        for campo in ESQUEMA_LECTURAS:
            invalido = self.df.withColumn(campo.name, F.lit(None).cast(campo.dataType))
            with self.subTest(campo=campo.name), self.assertRaisesRegex(ValueError, "nulos"):
                s01(invalido, zona_id="NO-EXISTE")

    def test_cadenas_vacias_y_columnas_repetidas(self):
        for campo in (c for c in ESQUEMA_LECTURAS if isinstance(c.dataType, T.StringType)):
            with self.subTest(campo=campo.name), self.assertRaisesRegex(ValueError, "cadenas vacías"):
                s01(self.df.withColumn(campo.name, F.lit("  ")))
        with self.assertRaisesRegex(ValueError, "Columnas repetidas"):
            s01(self.df.select("*", "sensor_id"))

    def test_parametros_invalidos(self):
        for filtros in ({"desde": "2025-01-01"}, {"desde": "invalida"},
                        {"desde": DIA["hasta"], "hasta": DIA["desde"]},
                        {"desde": DIA["desde"], "hasta": DIA["desde"]},
                        {"zona_id": " "}, {"zona_id": 1}, {"sintetico": "false"}, {"sintetico": 0}):
            with self.subTest(filtros=filtros), self.assertRaises(ValueError):
                s01(self.df, **filtros)

    def test_sesion_debe_ser_utc(self):
        self.sesion.conf.set("spark.sql.session.timeZone", "America/Costa_Rica")
        try:
            with self.assertRaisesRegex(ValueError, "timeZone=UTC"):
                s01(self.df)
        finally:
            self.sesion.conf.set("spark.sql.session.timeZone", "UTC")

    def test_precision_signo_y_muestra_sintetica(self):
        self.assertEqual(self.df.schema["valor"].dataType, T.DecimalType(18, 6))
        valores = {r.lectura_id: r.valor for r in self.df.select("lectura_id", "valor").collect()}
        self.assertEqual(valores["muestra:DEMO-L001"], Decimal("-0.125000"))
        self.assertEqual(valores["muestra:DEMO-L002"], Decimal("12.345678"))
        self.assertEqual(self.df.where(~F.col("sintetico")).count(), 0)

    def test_lectura_parquet(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = str(Path(temporal) / "lecturas")
            self.df.write.parquet(ruta)
            self.assertEqual(self.resultado(leer_lecturas(self.sesion, ruta, "parquet")), self.resultado())

    def test_jsonl_vacio(self):
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "vacio.jsonl"
            ruta.touch()
            self.assertEqual(self.resultado(leer_lecturas(self.sesion, str(ruta), "jsonl")), [])

    def test_jsonl_invalido_no_redondea_ni_repara(self):
        fila = json.loads(MUESTRA.read_text(encoding="utf-8").splitlines()[0])
        for campo, valor in (("valor", "0.1234567"), ("valor", "1000000000000"),
                             ("valor", "NaN"), ("valor", None),
                             ("fecha_utc", "2025-01-01T00:00:00"),
                             ("fecha_utc", "2025-02-30T00:00:00Z")):
            with self.subTest(campo=campo, valor=valor), tempfile.TemporaryDirectory() as temporal:
                ruta = Path(temporal) / "invalido.jsonl"
                ruta.write_text(json.dumps({**fila, campo: valor}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    s01(leer_lecturas(self.sesion, str(ruta), "jsonl"))


if __name__ == "__main__":
    unittest.main()
