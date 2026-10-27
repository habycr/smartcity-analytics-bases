#!/usr/bin/env python3
"""Exporta una muestra EPA real y la importa en una BD nueva con 01_schema.sql."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import sys
import traceback
from pathlib import Path

TABLES = {
    'categoria_sensor': ('id_categoria', 'nombre_categoria'),
    'tipo_sensor': ('tipo_sensor', 'id_categoria'),
    'organismo_responsable': ('id_organismo', 'nombre', 'responsable'),
    'ubicacion': ('id_ubicacion', 'nombre_zona', 'distrito', 'latitud', 'longitud'),
    'variable_medicion': ('id_variable', 'nombre_variable', 'unidad_canonica'),
    'sensor': ('id_sensor', 'nombre', 'tipo_sensor', 'fecha_instalacion', 'estado', 'id_ubicacion', 'id_organismo'),
    'medicion': ('id_medicion', 'id_sensor', 'id_variable', 'fecha_utc', 'valor', 'fuente'),
}


def connect(dsn):
    try:
        import psycopg2
    except ImportError as error:
        raise RuntimeError('Instala psycopg2: sudo apt install python3-psycopg2') from error
    return psycopg2.connect(dsn)


def export_sample(conn, folder: Path, limit: int):
    if limit < 1:
        raise ValueError('--max-mediciones debe ser mayor que cero')
    folder.mkdir(parents=True, exist_ok=True)
    counts = {}
    with conn:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL TIME ZONE 'UTC'")
            # Tabla temporal: máximo una fila por sensor primero; después más filas,
            # orden estable y sin duplicar IDs. Esto mantiene diversidad entre sensores.
            cur.execute('''
                CREATE TEMP TABLE sample_medicion_ids ON COMMIT DROP AS
                SELECT id_medicion FROM (
                    SELECT id_medicion, id_sensor, fecha_utc,
                           ROW_NUMBER() OVER (PARTITION BY id_sensor ORDER BY fecha_utc, id_medicion) AS orden_sensor
                    FROM public.medicion
                    WHERE fuente = %s AND id_sensor LIKE %s
                ) t ORDER BY orden_sensor, id_sensor, fecha_utc, id_medicion LIMIT %s
            ''', ('EPA AQS hourly 2025', 'EPA-%', limit))
            cur.execute('CREATE UNIQUE INDEX ON sample_medicion_ids(id_medicion)')
            queries = {
                'medicion': 'SELECT m.* FROM public.medicion m JOIN sample_medicion_ids a USING(id_medicion)',
                'sensor': 'SELECT DISTINCT s.* FROM public.sensor s JOIN public.medicion m ON m.id_sensor=s.id_sensor JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
                'ubicacion': 'SELECT DISTINCT u.* FROM public.ubicacion u JOIN public.sensor s ON s.id_ubicacion=u.id_ubicacion JOIN public.medicion m ON m.id_sensor=s.id_sensor JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
                'organismo_responsable': 'SELECT DISTINCT o.* FROM public.organismo_responsable o JOIN public.sensor s ON s.id_organismo=o.id_organismo JOIN public.medicion m ON m.id_sensor=s.id_sensor JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
                'tipo_sensor': 'SELECT DISTINCT t.* FROM public.tipo_sensor t JOIN public.sensor s ON s.tipo_sensor=t.tipo_sensor JOIN public.medicion m ON m.id_sensor=s.id_sensor JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
                'categoria_sensor': 'SELECT DISTINCT c.* FROM public.categoria_sensor c JOIN public.tipo_sensor t ON t.id_categoria=c.id_categoria JOIN public.sensor s ON s.tipo_sensor=t.tipo_sensor JOIN public.medicion m ON m.id_sensor=s.id_sensor JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
                'variable_medicion': 'SELECT DISTINCT v.* FROM public.variable_medicion v JOIN public.medicion m ON m.id_variable=v.id_variable JOIN sample_medicion_ids a ON a.id_medicion=m.id_medicion',
            }
            for table, columns in TABLES.items():
                out = folder / f'{table}.csv'
                col_sql = ', '.join(f'"{c}"' for c in columns)
                order_sql = ', '.join(f'q."{c}"' for c in (columns[0],))
                query = f'SELECT {col_sql} FROM ({queries[table]}) q ORDER BY {order_sql}'
                with out.open('w', newline='', encoding='utf-8') as handle:
                    # PostgreSQL COPY respeta CSV (comillas, nulos y números) y hace streaming.
                    cur.copy_expert(f'COPY ({query}) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING \'UTF8\')', handle)
                with out.open(newline='', encoding='utf-8') as handle:
                    counts[table] = sum(1 for _ in csv.DictReader(handle))
                print(f'{out.name}: {counts[table]} filas')
    manifest = {'origen': 'PostgreSQL local, registros EPA AQS 2025 existentes',
                'seleccion': 'orden por número de lectura dentro de cada sensor; desempate determinista',
                'max_mediciones': limit, 'conteos': counts,
                'sha256': {f'{table}.csv': hashlib.sha256((folder / f'{table}.csv').read_bytes()).hexdigest()
                           for table in TABLES}}
    (folder / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return counts


def import_sample(conn, folder: Path):
    with conn:
        with conn.cursor() as cur:
            for table in TABLES:
                cur.execute(f'SELECT EXISTS(SELECT 1 FROM public."{table}" LIMIT 1)')
                if cur.fetchone()[0]:
                    raise RuntimeError('La BD destino debe tener el esquema vacío. Tabla no vacía: ' + table)
            for table, columns in TABLES.items():
                filepath = folder / f'{table}.csv'
                if not filepath.is_file():
                    raise FileNotFoundError(filepath)
                col_sql = ', '.join(f'"{c}"' for c in columns)
                with filepath.open('r', newline='', encoding='utf-8') as handle:
                    cur.copy_expert(f'COPY public."{table}" ({col_sql}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, ENCODING \'UTF8\')', handle)
                print(f'Importada {table}')
            # Restaurar las secuencias identity para futuras inserciones.
            for table, field in [('categoria_sensor','id_categoria'),('organismo_responsable','id_organismo'),('variable_medicion','id_variable'),('medicion','id_medicion')]:
                cur.execute('SELECT pg_get_serial_sequence(%s, %s)', (f'public.{table}', field))
                seq = cur.fetchone()[0]
                if seq:
                    cur.execute(f'SELECT MAX("{field}") FROM public."{table}"')
                    maximum = cur.fetchone()[0]
                    if maximum is not None and maximum > 0:
                        cur.execute('SELECT setval(%s, %s, true)', (seq, maximum))
            cur.execute('''SELECT COUNT(*) FROM public.medicion m
                           LEFT JOIN public.sensor s ON s.id_sensor=m.id_sensor
                           WHERE s.id_sensor IS NULL''')
            orphan = cur.fetchone()[0]
            if orphan:
                raise RuntimeError(f'Mediciones sin sensor: {orphan}')
            cur.execute('SELECT COUNT(*) FROM public.medicion')
            print('Mediciones verificadas:', cur.fetchone()[0], '| huérfanas: 0')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('accion', choices=('exportar','importar'))
    parser.add_argument('--dsn', required=True, help='DSN libpq, sin contraseña; usar ~/.pgpass')
    parser.add_argument('--directorio', type=Path, default=Path('postgres/datos_muestra'))
    parser.add_argument('--max-mediciones', type=int, default=3000)
    args = parser.parse_args()
    conn = None
    try:
        conn = connect(args.dsn)
        if args.accion == 'exportar':
            export_sample(conn, args.directorio, args.max_mediciones)
        else:
            import_sample(conn, args.directorio)
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        if conn is not None:
            conn.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
