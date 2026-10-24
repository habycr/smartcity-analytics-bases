#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

verificar() {
  local archivo="$1"
  local esperado="$2"

  mongosh "mongodb://127.0.0.1:27017/smartcity" --quiet --eval "
    let salida;
    globalThis.printjson = function (valor) {
      salida = valor;
    };

    load('$archivo');

    function normalizar(valor) {
      if (Array.isArray(valor)) {
        return valor.map(normalizar);
      }
      if (valor !== null && typeof valor === 'object') {
        return Object.fromEntries(
          Object.keys(valor).sort().map(
            clave => [clave, normalizar(valor[clave])]
          )
        );
      }
      return valor;
    }

    const esperado = $esperado;
    const obtenido = JSON.stringify(normalizar(salida));
    const referencia = JSON.stringify(normalizar(esperado));

    if (obtenido !== referencia) {
      throw new Error(
        'Resultado incorrecto en $archivo\n' +
        'Esperado: ' + referencia + '\n' +
        'Obtenido: ' + obtenido
      );
    }

    print('[PASS] $archivo');
  "
}

verificar mongo/consultas/Q05_alertas_zona.js '[
  {"zona_id":"Z001","cantidad_alertas":1},
  {"zona_id":"Z002","cantidad_alertas":1}
]'

verificar mongo/consultas/Q06_promedios_zona.js '[
  {"zona_id":"Z001","variable":"pm25","unidad":"µg/m³","promedio":30,"cantidad":2},
  {"zona_id":"Z001","variable":"temperatura","unidad":"°C","promedio":25,"cantidad":2},
  {"zona_id":"Z002","variable":"pm25","unidad":"µg/m³","promedio":40,"cantidad":2},
  {"zona_id":"Z002","variable":"temperatura","unidad":"°C","promedio":26,"cantidad":2}
]'

verificar mongo/consultas/Q07_promedios_tipo_sensor.js '[
  {"tipo_sensor":"particulas","variable":"pm25","unidad":"µg/m³","promedio":35,"cantidad":4},
  {"tipo_sensor":"termometro","variable":"temperatura","unidad":"°C","promedio":25.5,"cantidad":4}
]'

verificar mongo/consultas/Q08_incidentes_categoria.js '[
  {"categoria":"ambiental","cantidad_incidentes":2},
  {"categoria":"infraestructura","cantidad_incidentes":1}
]'

verificar mongo/consultas/Q09_evolucion_diaria.js '[
  {"dia":"2026-10-01","zona_id":"Z001","variable":"temperatura","unidad":"°C","promedio":20,"cantidad":1},
  {"dia":"2026-10-01","zona_id":"Z002","variable":"temperatura","unidad":"°C","promedio":24,"cantidad":1},
  {"dia":"2026-10-02","zona_id":"Z001","variable":"temperatura","unidad":"°C","promedio":30,"cantidad":1},
  {"dia":"2026-10-02","zona_id":"Z002","variable":"temperatura","unidad":"°C","promedio":28,"cantidad":1}
]'

echo "Las 5 consultas de agregacion devolvieron los resultados esperados."
