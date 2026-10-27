#!/usr/bin/env python3
"""ETL reproducible EPA AQS (PM2.5/PM10) -> SmartCity PostgreSQL 16.

Uso local (peer): sudo -u postgres python3 postgres/carga.py --datos /ruta/epa --dsn 'dbname=smartcity_pruebas'
Usa psycopg2 (Ubuntu: sudo apt install python3-psycopg2).
No descarga datos ni modifica el esquema. Los IDs negativos BIGINT quedan reservados a EPA.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

FILES = (("hourly_88101_2025.zip", "88101", "pm25", "Micrograms/cubic meter (LC)"),
         ("hourly_81102_2025.zip", "81102", "pm10", "Micrograms/cubic meter (25 C)"))
SOURCE = "EPA AQS hourly 2025"
CUT_OFF = date(2025, 10, 1)  # ventana final fija; no estado físico verificado
CATEGORY = "Calidad del aire (EPA)"
KIND = "particulas"
UNIT = "µg/m³"  # dimensión común; se mantienen condiciones de referencia por parámetro


def fetch_required(cursor, description: str):
    """Devuelve una fila obligatoria o falla explícitamente si no existe.

    psycopg2 tipa fetchone() como Optional[tuple]; validar None evita
    falsos positivos de Pylance y errores difíciles de interpretar.
    """
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError(f"No se encontró la fila esperada: {description}")
    return row


def rows_zip(path: Path):
    with zipfile.ZipFile(path) as archive:
        csv_files = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_files) != 1:
            raise ValueError(f"Se esperaba un CSV dentro de {path}: {csv_files}")
        with archive.open(csv_files[0]) as raw:
            stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            yield from csv.DictReader(stream)



def selected_rows(path: Path, limit: int, mode: str, total: int | None = None):
    """Produce (indice, fila) sin materializar CSV; posiciones equiespaciadas.

    En modo distribuida, para T filas y N=min(limite,T), toma las
    posiciones floor(k*T/N), k=0..N-1. Es determinista, cubre todo el
    archivo y conserva la selección al repetir la misma ejecución.
    """
    if mode == "primeras":
        for index, row in enumerate(rows_zip(path)):
            if index >= limit:
                break
            yield index, row
        return
    if total is None:
        raise ValueError("Se requiere el total de filas para muestreo distribuido")
    count = min(limit, total)
    if count == 0:
        return
    k = 0
    target = 0
    for index, row in enumerate(rows_zip(path)):
        if index == target:
            yield index, row
            k += 1
            if k == count:
                break
            target = (k * total) // count


def count_rows(path: Path) -> int:
    return sum(1 for _ in rows_zip(path))


def site_key(row):
    fields = (row.get("State Code", ""), row.get("County Code", ""),
              row.get("Site Num", row.get("Site Number", "")))
    if any(not x.strip() for x in fields):
        return None
    return "EPA-" + "-".join(x.strip() for x in fields)


def sensor_key(row):
    station = site_key(row)
    parameter = (row.get("Parameter Code") or "").strip()
    poc = (row.get("POC") or "").strip()
    if not station or not parameter or not poc:
        return None
    return f"{station}-{parameter}-{poc}"


def stable_measurement_id(sensor, parameter, instant):
    """BIGINT negativo estable: no choca con IDENTITY ni IDs DEMO positivos."""
    raw = f"EPA-AQS|{sensor}|{parameter}|{instant.isoformat()}".encode("utf-8")
    number = int.from_bytes(hashlib.blake2b(raw, digest_size=8).digest(), "big")
    return -(number % (2**63 - 1) + 1)


def parse_measurement(row, parameter, expected_unit, stats):
    sensor = sensor_key(row)
    if not sensor or (row.get("Parameter Code") or "").strip() != parameter:
        stats["clave_sensor_invalida"] += 1
        return None
    if (row.get("Units of Measure") or "").strip() != expected_unit:
        stats["unidad_no_esperada"] += 1
        return None
    try:
        instant = datetime.strptime((row["Date GMT"] + " " + row["Time GMT"]).strip(),
                                    "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except (ValueError, KeyError):
        stats["fecha_invalida"] += 1
        return None
    try:
        value = Decimal((row.get("Sample Measurement") or "").strip())
        if not value.is_finite() or abs(value) >= Decimal("1e12"):
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        stats["valor_invalido"] += 1
        return None
    if value < 0:
        stats["negativos_conservados"] += 1
    if (row.get("Qualifier") or "").strip():
        stats["con_calificador_conservados"] += 1
    return sensor, instant, value


def get_index(cursor, table, key_name, id_name):
    cursor.execute(f"SELECT {id_name}, {key_name} FROM public.{table}")
    return {key: pk for pk, key in cursor.fetchall()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datos", type=Path, required=True, help="directorio con ZIP EPA AQS")
    p.add_argument("--dsn", default=os.environ.get("SMARTCITY_PG_DSN", "dbname=smartcity_pruebas"),
                   help="cadena libpq; no escribir contraseña en línea de comandos")
    p.add_argument("--por-archivo", type=int, default=5000,
                   help="máximo N filas seleccionadas de cada archivo (5000 => hasta 10000)")
    p.add_argument("--muestreo", choices=("primeras", "distribuida"), default="primeras",
                   help="primeras: primeras N filas; distribuida: N posiciones espaciadas a lo largo del ZIP")
    p.add_argument("--lote", type=int, default=1000, help="tamaño de lote de inserciones")
    p.add_argument("--informe", type=Path, default=Path("carga_epa_reporte.json"))
    args = p.parse_args()
    if args.por_archivo < 1 or args.lote < 1:
        p.error("--por-archivo y --lote deben ser >= 1")
    for fname in ("aqs_sites.zip", "aqs_monitors.zip", *(x[0] for x in FILES)):
        if not (args.datos / fname).is_file():
            p.error(f"Falta {args.datos / fname}")
    try:
        import psycopg2
        from psycopg2.extras import execute_values
    except ImportError:
        p.error("Falta psycopg2: sudo apt install python3-psycopg2 (Ubuntu)")

    stats = Counter()
    requested = set()
    totals = {}
    print("1/4 Identificando monitores usados por la muestra...")
    for fname, parameter, _, _ in FILES:
        if args.muestreo == "distribuida":
            print(f"  Contando filas de {fname} (lectura en streaming)...", flush=True)
            totals[fname] = count_rows(args.datos / fname)
            print(f"    Filas disponibles: {totals[fname]}", flush=True)
        for _, row in selected_rows(args.datos / fname, args.por_archivo,
                                    args.muestreo, totals.get(fname)):
            stats[f"filas_seleccionadas_{parameter}"] += 1
            key = sensor_key(row)
            if key:
                requested.add(key)
    print(f"  Monitores distintos seleccionados: {len(requested)}")

    monitors = {}
    required_sites = set()
    print("2/4 Leyendo catálogo oficial de monitores y estaciones...")
    for row in rows_zip(args.datos / "aqs_monitors.zip"):
        key = sensor_key(row)
        if key in requested:
            monitors[key] = row
            required_sites.add(site_key(row))
    sites = {}
    for row in rows_zip(args.datos / "aqs_sites.zip"):
        key = site_key(row)
        if key in required_sites:
            sites[key] = row
    stats["monitores_no_en_catalogo"] = len(requested - monitors.keys())
    stats["estaciones_no_en_catalogo"] = len(required_sites - sites.keys())
    accepted_sites = {}
    for key, row in sites.items():
        try:
            latitude, longitude = Decimal(row["Latitude"]), Decimal(row["Longitude"])
            if not (latitude.is_finite() and longitude.is_finite() and
                    -90 <= latitude <= 90 and -180 <= longitude <= 180):
                raise ValueError
        except (InvalidOperation, KeyError, ValueError):
            stats["estaciones_coordenadas_invalidas"] += 1
            continue
        zone = (row.get("Local Site Name") or "").strip() or f"Estación {key} (nombre generado)"
        district = (row.get("County Name") or "").strip() or "Condado no indicado"
        accepted_sites[key] = (key, zone[:150], district[:120], latitude, longitude)

    # Atributos incompletos: no inventar responsables; descartar registros sin organismo verificable.
    accepted_monitors = {}
    agencies = set()
    for key, row in monitors.items():
        station = site_key(row)
        if station not in accepted_sites:
            stats["monitores_estacion_invalida"] += 1
            continue
        agency = ((row.get("Collecting Agency") or "").strip() or
                  (row.get("Reporting Agency") or "").strip() or
                  (sites[station].get("Owning Agency") or "").strip())
        if not agency:
            stats["monitores_sin_organismo"] += 1
            continue
        if len(agency) > 180:
            stats["monitores_organismo_demasiado_largo"] += 1
            continue
        last_date = (row.get("Last Sample Date") or "").strip()
        try:
            sampled = date.fromisoformat(last_date) if last_date else None
        except ValueError:
            sampled = None
        state = "activo" if sampled is not None and sampled >= CUT_OFF else "inactivo"
        name = f"Monitor EPA {row.get('Parameter Name', 'partículas')} {key}"[:150]
        accepted_monitors[key] = (key, name, KIND, None, state, station, agency)
        agencies.add(agency)

    print("3/4 Insertando catálogos y sensores...")
    report = {"origen": "EPA AQS, archivos horarios 2025", "limite_por_archivo": args.por_archivo,
              "modo_muestreo": args.muestreo,
              "filas_disponibles_por_archivo": totals if args.muestreo == "distribuida" else None,
              "politica": {"identificador_medicion": "BIGINT negativo BLAKE2b(sensor,parametro,UTC)",
                           "fecha_instalacion": "NULL (desconocida)",
                           "estado": "activo si Last Sample Date >= 2025-10-01; no estado físico",
                           "organismo": "Collecting > Reporting > Owning; rol puede variar",
                           "mediciones_negativas": "conservadas sin alteración",
                           "calificadores": "conservados solo en ZIP original; no filtrados",
                           "unidades_origen": {a: u for _, a, _, u in FILES},
                           "unidad_canonica_en_bd": UNIT,
                           "muestreo": ("primeras N filas por archivo; posible sesgo geográfico"
                                        if args.muestreo == "primeras" else
                                        "N posiciones equiespaciadas por índice en todo el archivo; "
                                        "determinista, no aleatorio ni estratificado; "
                                        "la distribución depende del orden del CSV")}}
    try:
        conn = psycopg2.connect(args.dsn)
        with conn:
            with conn.cursor() as cur:
                # Una ejecución a la vez; las filas por lotes siguen siendo una sola transacción atómica.
                cur.execute("SELECT pg_advisory_xact_lock(hashtext('smartcity_epa_carga_v1'))")
                cur.execute("SET LOCAL TIME ZONE 'UTC'")
                cur.execute("INSERT INTO public.categoria_sensor(nombre_categoria) VALUES (%s) "
                            "ON CONFLICT(nombre_categoria) DO NOTHING", (CATEGORY,))
                cur.execute("SELECT id_categoria FROM public.categoria_sensor WHERE nombre_categoria=%s", (CATEGORY,))
                category_id = fetch_required(cur, f"categoria_sensor {CATEGORY}")[0]
                cur.execute("INSERT INTO public.tipo_sensor(tipo_sensor,id_categoria) VALUES (%s,%s) "
                            "ON CONFLICT(tipo_sensor) DO NOTHING", (KIND, category_id))
                cur.execute("SELECT id_categoria FROM public.tipo_sensor WHERE tipo_sensor=%s", (KIND,))
                if fetch_required(cur, f"tipo_sensor {KIND}")[0] != category_id:
                    raise RuntimeError("tipo_sensor=particulas existe asociado a otra categoría")

                variables = {}
                for _, parameter, name, _ in FILES:
                    cur.execute("INSERT INTO public.variable_medicion(nombre_variable,unidad_canonica) "
                                "VALUES (%s,%s) ON CONFLICT(nombre_variable) DO NOTHING", (name, UNIT))
                    cur.execute("SELECT id_variable,unidad_canonica FROM public.variable_medicion "
                                "WHERE nombre_variable=%s", (name,))
                    vid, existing_unit = fetch_required(cur, f"variable_medicion {name}")
                    if existing_unit != UNIT:
                        raise RuntimeError(f"Unidad distinta para {name}: {existing_unit}")
                    variables[parameter] = vid

                cur.execute("SELECT id_organismo,nombre FROM public.organismo_responsable "
                            "WHERE nombre=ANY(%s) ORDER BY id_organismo", (sorted(agencies),))
                agency_ids = {}
                for identifier, name in cur.fetchall():
                    agency_ids.setdefault(name, identifier)
                for name in sorted(agencies - agency_ids.keys()):
                    cur.execute("INSERT INTO public.organismo_responsable(nombre,responsable) "
                                "VALUES (%s,NULL) RETURNING id_organismo", (name,))
                    agency_ids[name] = fetch_required(cur, f"organismo_responsable {name}")[0]
                    stats["organismos_insertados"] += 1
                for key, name, district, lat, lon in accepted_sites.values():
                    cur.execute("INSERT INTO public.ubicacion(id_ubicacion,nombre_zona,distrito,latitud,longitud) "
                                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT(id_ubicacion) DO NOTHING",
                                (key, name, district, lat, lon))
                    stats["ubicaciones_insertadas"] += cur.rowcount
                for key, name, kind, installation, state, station, agency in accepted_monitors.values():
                    cur.execute("INSERT INTO public.sensor "
                                "(id_sensor,nombre,tipo_sensor,fecha_instalacion,estado,id_ubicacion,id_organismo) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(id_sensor) DO NOTHING",
                                (key, name, kind, installation, state, station, agency_ids[agency]))
                    stats["sensores_insertados"] += cur.rowcount

                print("4/4 Cargando mediciones con lotes y PK estable...")
                statement = ("INSERT INTO public.medicion "
                             "(id_medicion,id_sensor,id_variable,fecha_utc,valor,fuente) VALUES %s "
                             "ON CONFLICT(id_medicion) DO NOTHING")
                for fname, parameter, _, original_unit in FILES:
                    buffer = []
                    for _, row in selected_rows(args.datos / fname, args.por_archivo,
                                                args.muestreo, totals.get(fname)):
                        parsed = parse_measurement(row, parameter, original_unit, stats)
                        if parsed is None:
                            continue
                        key, instant, value = parsed
                        if key not in accepted_monitors:
                            stats["mediciones_sin_sensor_aceptado"] += 1
                            continue
                        buffer.append((stable_measurement_id(key, parameter, instant), key,
                                       variables[parameter], instant, value, SOURCE))
                        if len(buffer) >= args.lote:
                            execute_values(cur, statement, buffer, page_size=args.lote)
                            stats["filas_intentadas"] += len(buffer)
                            stats["mediciones_insertadas"] += cur.rowcount
                            buffer.clear()
                    if buffer:
                        execute_values(cur, statement, buffer, page_size=args.lote)
                        stats["filas_intentadas"] += len(buffer)
                        stats["mediciones_insertadas"] += cur.rowcount
                    print(f"  Procesado {fname}")
        conn.close()
    except Exception as exc:
        print(f"ERROR: transacción revertida: {exc}", file=sys.stderr)
        return 1

    report["conteos"] = dict(sorted(stats.items()))
    report["resultado"] = "COMMIT correcto"
    args.informe.parent.mkdir(parents=True, exist_ok=True)
    args.informe.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Carga completada. Nuevas mediciones: {stats['mediciones_insertadas']}; "
          f"intentadas: {stats['filas_intentadas']}; informe: {args.informe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
