"""Carga reproducible SmartCity / MongoDB (Edward, sprint 1).

Fuentes admitidas: CSV normalizado y ZIP/CSV EPA AQS hourly.
La integridad cruzada exige un catalogo exportado de PostgreSQL.
Nunca inventa sensores o zonas y no representa datos sinteticos como reales.
Uso y limitaciones: docs/ejecucion_mongo.md y docs/fuentes_y_generacion.md.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
import random
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path

from bson.decimal128 import Decimal128
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

CANONICAL = {"88101": "pm25", "81102": "pm10"}
FUENTE_EPA = "EPA AQS hourly 2025"
UNIDAD = "µg/m³"
PRECISION = Decimal("0.000001")


def texto(fila, *claves):
    for c in claves:
        valor = fila.get(c)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return ""


def decimal_valido(valor):
    try:
        d = Decimal(str(valor))
        if not d.is_finite():
            raise ValueError("Numero no finito")
        return d.quantize(PRECISION, rounding=ROUND_HALF_EVEN)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"Valor numerico invalido: {valor!r}") from exc


def fecha_utc(texto_fecha):
    try:
        d = datetime.fromisoformat(texto_fecha.strip().replace("Z", "+00:00"))
        if d.tzinfo is None:
            raise ValueError("Fecha sin zona horaria (se requiere UTC explicito)")
        return d.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Fecha UTC invalida: {texto_fecha!r}") from exc


def identificador(doc, nonce=""):
    campos = [doc["sensor_id"], doc["variable"], doc["fecha_utc"].isoformat(),
              doc["fuente"], str(doc["sintetico"]), nonce]
    serial = "|".join(campos).encode("utf-8")
    return "SC-" + hashlib.sha256(serial).hexdigest()[:40]


def cargar_catalogo(path):
    catalogo = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as fp:
        lector = csv.DictReader(fp)
        for fila in lector:
            sensor = texto(fila, "id_sensor", "sensor_id")
            zona = texto(fila, "id_ubicacion", "zona_id")
            if not sensor or not zona:
                raise ValueError("El catalogo requiere columnas id_sensor e id_ubicacion")
            if sensor in catalogo and catalogo[sensor] != zona:
                raise ValueError(f"Sensor repetido con zonas distintas: {sensor}")
            catalogo[sensor] = zona
    if not catalogo:
        raise ValueError("Catalogo vacio")
    return catalogo


def normalizar(fila):
    """Normaliza UNA fila. Retorna None si no es PM2.5/PM10 en bruto EPA."""
    if "State Code" in fila and "Parameter Code" in fila:
        parametro = texto(fila, "Parameter Code")
        if parametro not in CANONICAL:
            return None
        estado = texto(fila, "State Code")
        condado = texto(fila, "County Code")
        sitio = texto(fila, "Site Num", "Site Number")
        poc = texto(fila, "POC")
        if not all((estado, condado, sitio, poc)):
            raise ValueError("Faltan componentes de identificador EPA")
        zona = f"EPA-{estado}-{condado}-{sitio}"
        sensor = f"{zona}-{parametro}-{poc}"
        fecha = datetime.strptime(
            f'{texto(fila, "Date GMT")} {texto(fila, "Time GMT")}',
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)
        valor = decimal_valido(texto(fila, "Sample Measurement"))
        doc = {
            "sensor_id": sensor, "zona_id": zona,
            "tipo_sensor": "particulas", "variable": CANONICAL[parametro],
            "valor": Decimal128(valor), "unidad": UNIDAD,
            "fecha_utc": fecha, "fuente": FUENTE_EPA, "sintetico": False,
            "procedencia": {
                "parametro_epa": parametro, "poc": poc,
                "unidad_original": texto(fila, "Units of Measure")
            }
        }
        calificador = texto(fila, "Qualifier", "Qualifiers")
        if calificador:
            doc["calidad"] = {"calificador_epa": calificador}
        return doc

    sensor = texto(fila, "sensor_id")
    zona = texto(fila, "zona_id")
    variable = texto(fila, "variable")
    if not sensor or not zona or not variable:
        raise ValueError("CSV normalizado requiere sensor_id, zona_id, variable")
    sintetico = texto(fila, "sintetico").lower()
    if sintetico not in ("true", "false"):
        raise ValueError("Campo sintetico debe ser true/false")
    unidad = texto(fila, "unidad")
    tipo = texto(fila, "tipo_sensor")
    if variable in ("pm25", "pm10") and unidad != UNIDAD:
        raise ValueError(f"Unidad incompatible para {variable}: {unidad!r}")
    if not tipo or not unidad or not texto(fila, "fuente"):
        raise ValueError("Faltan tipo_sensor, unidad o fuente")
    return {
        "sensor_id": sensor, "zona_id": zona,
        "tipo_sensor": tipo, "variable": variable,
        "valor": Decimal128(decimal_valido(texto(fila, "valor"))),
        "unidad": unidad, "fecha_utc": fecha_utc(texto(fila, "fecha_utc")),
        "fuente": texto(fila, "fuente"), "sintetico": sintetico == "true"
    }


def iterar_archivo(path):
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archivo:
            nombres = sorted(n for n in archivo.namelist() if n.lower().endswith(".csv"))
            if not nombres:
                raise ValueError(f"ZIP sin archivos .csv: {path}")
            for nombre in nombres:
                with archivo.open(nombre) as raw:
                    with io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="") as fp:
                        yield from csv.DictReader(fp)
    elif path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as fp:
            yield from csv.DictReader(fp)
    else:
        raise ValueError(f"Se requiere .csv o .zip: {path}")


def insertar_lote(coleccion, docs):
    if not docs:
        return 0, 0
    operaciones = [UpdateOne({"_id": d["_id"]}, {"$setOnInsert": d}, upsert=True) for d in docs]
    resultado = coleccion.bulk_write(operaciones, ordered=False)
    return resultado.upserted_count, resultado.matched_count


def generar_sintetico(ejemplo, numero, rng):
    doc = dict(ejemplo)
    base_valor = ejemplo["valor"].to_decimal()
    # Variacion aleatoria reproducible (2% de la magnitud, nunca datos reales).
    variacion = Decimal(str(rng.uniform(-0.02, 0.02)))
    valor = (base_valor * (Decimal(1) + variacion)).quantize(PRECISION, rounding=ROUND_HALF_EVEN)
    doc["valor"] = Decimal128(valor)
    doc["fecha_utc"] = ejemplo["fecha_utc"] + timedelta(days=numero % 28, minutes=(numero * 37) % 59 + 1)
    doc["fuente"] = "SIMULACION derivada EPA/DEMO"
    doc["sintetico"] = True
    doc["procedencia"] = {"base_documento": ejemplo["_id"], "metodo": "variacion_2pct_y_desplazamiento_temporal", "semilla": 3101}
    doc.pop("calidad", None)
    doc["_id"] = identificador(doc, nonce=f"SIM-{numero:012d}")
    return doc


def main():
    load_dotenv()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--archivo", action="append", required=True, help="CSV o ZIP EPA; repetir para mas archivos")
    p.add_argument("--catalogo", required=True, help="CSV exportado de PostgreSQL: id_sensor,id_ubicacion")
    p.add_argument("--bd", default=os.environ.get("SMARTCITY_DB", "smartcity_demo"))
    p.add_argument("--uri", default=os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"))
    p.add_argument("--lote", type=int, default=1000)
    p.add_argument("--limite-reales", type=int, default=0, help="0=sin limite")
    p.add_argument("--objetivo", type=int, default=0, help="Completar N lecturas mediante generacion sintética marcada")
    p.add_argument("--reporte", help="Ruta opcional del reporte JSON")
    args = p.parse_args()
    if args.lote < 1 or args.objetivo < 0 or args.limite_reales < 0:
        p.error("--lote debe ser positivo; --objetivo y --limite-reales no pueden ser negativos")
    if args.bd == "smartcity" and Path(args.catalogo).name.lower().startswith("catalogo_demo"):
        p.error("Bloqueado: el catalogo DEMO no debe usarse con la base de produccion")
    catalogo = cargar_catalogo(args.catalogo)
    cliente = MongoClient(args.uri, serverSelectionTimeoutMS=8000)
    cliente.admin.command("ping")
    base = cliente[args.bd]
    if "lecturas" not in base.list_collection_names():
        raise RuntimeError("Primero ejecuta mongo/01_colecciones.js en la misma base")
    col = base["lecturas"]
    estadisticas = {"archivos": args.archivo, "base": args.bd, "filas_leidas":0,
        "filas_validas":0,"omitidas_sin_catalogo":0,"omitidas_otros_parametros":0,
        "filas_invalidas":0,"errores_muestra":[],"insertadas":0,"ya_existentes":0,
        "sinteticas_insertadas":0,"semilla":3101}
    lote=[]
    bases=[]
    detener=False
    for archivo in args.archivo:
        for fila in iterar_archivo(archivo):
            estadisticas["filas_leidas"] += 1
            try:
                doc = normalizar(fila)
                if doc is None:
                    estadisticas["omitidas_otros_parametros"] += 1
                    continue
                if catalogo.get(doc["sensor_id"]) != doc["zona_id"]:
                    estadisticas["omitidas_sin_catalogo"] += 1
                    continue
                doc["_id"] = identificador(doc)
                estadisticas["filas_validas"] += 1
                if len(bases) < 3000:
                    bases.append(doc)
                lote.append(doc)
                if len(lote) >= args.lote:
                    n, m = insertar_lote(col, lote)
                    estadisticas["insertadas"] += n
                    estadisticas["ya_existentes"] += m
                    lote.clear()
                if args.limite_reales and estadisticas["filas_validas"] >= args.limite_reales:
                    detener=True
                    break
            except (ValueError, ArithmeticError) as exc:
                estadisticas["filas_invalidas"] += 1
                if len(estadisticas["errores_muestra"]) < 8:
                    estadisticas["errores_muestra"].append(str(exc))
        if detener:
            break
    n, m = insertar_lote(col, lote)
    estadisticas["insertadas"] += n
    estadisticas["ya_existentes"] += m
    lote.clear()
    if args.objetivo:
        if not bases:
            raise RuntimeError("No hay lecturas validas para ampliar; revisar catalogo y archivos")
        rng = random.Random(3101)
        actual = col.count_documents({})
        if actual < args.objetivo:
            # Recorremos la misma secuencia aleatoria al reanudar la carga:
            # los IDs de sintéticos son estables y los upserts evitan duplicados.
            max_intentos = args.objetivo * 3
            for i in range(max_intentos):
                if actual >= args.objetivo:
                    break
                d = generar_sintetico(rng.choice(bases), i, rng)
                lote.append(d)
                if len(lote) >= args.lote or i == max_intentos - 1:
                    n, _ = insertar_lote(col, lote)
                    actual += n
                    estadisticas["sinteticas_insertadas"] += n
                    lote.clear()
            if actual < args.objetivo:
                raise RuntimeError(f"Objetivo no alcanzado: {actual} / {args.objetivo}")
    estadisticas["lecturas_finales"] = col.count_documents({})
    estadisticas["lecturas_reales_finales"] = col.count_documents({"sintetico":False})
    estadisticas["lecturas_sinteticas_finales"] = col.count_documents({"sintetico":True})
    estadisticas["tamano_bytes_bson_documentos"] = base.command("collStats", "lecturas").get("size",0)
    texto_reporte = json.dumps(estadisticas, ensure_ascii=False, indent=2)
    print(texto_reporte)
    if args.reporte:
        Path(args.reporte).parent.mkdir(parents=True, exist_ok=True)
        Path(args.reporte).write_text(texto_reporte + "\n", encoding="utf-8")
    cliente.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
