import json
from pathlib import Path

import pandas as pd

rows = []

for file in Path("data/resultados").rglob("*.json"):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)

    tot = data["totales"]
    meta = data["metadata_loc"]

    rows.append(
        {
            "snapshot": file.parts[2].split("=")[1],
            "ambito": meta["ambito"],
            "dep_ubigeo": meta["dep_ubigeo"],
            "prov_ubigeo": meta["prov_ubigeo"],
            "ubigeo": meta["ubigeo"],
            "departamento": meta["dep_name"],
            "provincia": meta["prov_name"],
            "nombre": meta["nombre"],
            "total_votos_emitidos": tot["totalVotosEmitidos"],
            "total_votos_validos": tot["totalVotosValidos"],
            "participacion_ciudadana": tot["participacionCiudadana"],
            "actas_contabilizadas_pct": tot["actasContabilizadas"],
            "actas_contabilizadas": tot["contabilizadas"],
            "total_actas": tot["totalActas"],
            "fecha_actualizacion": tot["fechaActualizacion"],
        }
    )

silver_resultados = pd.DataFrame(rows)
