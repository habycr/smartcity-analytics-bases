"""Concilia los IDs y zonas de MongoDB con catalogo CSV exportado de PostgreSQL.

Excluye lecturas sinteticas por defecto. No reemplaza la comparacion fila a fila
con PostgreSQL ni el control de versiones de observaciones.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient


def main():
    load_dotenv()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalogo',required=True)
    p.add_argument('--bd',default=os.environ.get('SMARTCITY_DB','smartcity_demo'))
    p.add_argument('--uri',default=os.environ.get('MONGO_URI','mongodb://127.0.0.1:27017/'))
    p.add_argument('--incluir-sinteticos',action='store_true')
    args=p.parse_args()
    # Importarlo desde la misma carpeta cuando se ejecuta como archivo.
    from carga import cargar_catalogo
    catalogo=cargar_catalogo(args.catalogo)
    client=MongoClient(args.uri,serverSelectionTimeoutMS=8000)
    client.admin.command('ping')
    lectura=client[args.bd]['lecturas']
    filtro={} if args.incluir_sinteticos else {'sintetico':False}
    pipeline=[{'$match':filtro},{'$group':{
      '_id':{'sensor':'$sensor_id','zona':'$zona_id','variable':'$variable','unidad':'$unidad','tipo':'$tipo_sensor'},
      'n':{'$sum':1}}}]
    grupos=list(lectura.aggregate(pipeline,allowDiskUse=True))
    errores=[]
    revisadas=0
    for grupo in grupos:
        d=grupo['_id'];revisadas+=grupo['n']
        if catalogo.get(d['sensor']) != d['zona']:
            errores.append({'problema':'sensor sin catalogo o zona discordante',**d,'n':grupo['n']})
        if d['variable'] in ('pm25','pm10') and (d['unidad']!='µg/m³' or d['tipo']!='particulas'):
            errores.append({'problema':'tipo o unidad incorrectos para EPA',**d,'n':grupo['n']})
    informe={'base':args.bd,'documentos_revisados':revisadas,'grupos':len(grupos),'errores':len(errores),'ejemplos':errores[:15]}
    print(json.dumps(informe,ensure_ascii=False,indent=2))
    client.close()
    if errores:sys.exit(2)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'ERROR: {exc}',file=sys.stderr);sys.exit(1)
