import json
import time
import unicodedata
from pathlib import Path

import pandas as pd
import requests
import tqdm
from rich import print

DATA = Path("data")
BASE_DIR = DATA / "resultados\snapshot=20260630_142121"
OUTPUT_DIR = DATA / "last_review" / "geometry" / "dist"
CACHE_DIR = DATA / "last_review" / "geometry" / "prov"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

GEO_PROVINCIA_BASE_URL = (
    "https://resultadosegundavuelta.onpe.gob.pe/assets/lib/amcharts5/"
    "geodata/json/{type}/{prov_ubigeo}.json"
)
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Referer": "https://resultadosegundavuelta.onpe.gob.pe/main/presidenciales",
}

SLEEP_BETWEEN_REQUESTS = 0.25  # segundos, para no saturar el servidor


def normalize(s: str) -> str:
    """Mayúsculas, sin tildes, sin espacios extremos."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.upper().strip()


PARTY_NAME_MAP = {
    normalize("JUNTOS POR EL PERÚ"): "JP",
    normalize("FUERZA POPULAR"): "FP",
}
# Colores de partido pedidos: naranja para FP, verde para JP
PARTY_COLOR = {
    "FP": "#FF7F00",  # naranja
    "JP": "#1B7A3D",  # verde
}


# ---------------------------------------------------------------------------
# Paso 1: construir la tabla de resultados
# ---------------------------------------------------------------------------


def find_dist_files(base_dir: Path):
    return sorted(base_dir.rglob("dist=*.json"))


def build_table(base_dir: Path) -> pd.DataFrame:
    rows = []
    files = find_dist_files(base_dir)
    print(f"  Encontrados {len(files)} archivos dist=*.json")

    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            print(f"  [WARN] No se pudo leer {f}: {e}")
            continue

        meta = data.get("metadata_loc", {}) or {}
        ubigeo = meta.get("ubigeo")
        prov_ubigeo = meta.get("prov_ubigeo")
        dep_ubigeo = meta.get("dep_ubigeo")
        ambito = meta.get("ambito")

        for p in data.get("participantes", []):
            nombre = p.get("nombreAgrupacionPolitica", "") or ""
            partido = PARTY_NAME_MAP.get(normalize(nombre))
            if partido is None:
                # Solo nos interesan JP y FP, según lo pedido
                continue

            rows.append(
                {
                    "ubigeo": ubigeo,
                    "prov_ubigeo": prov_ubigeo,
                    "ambito": ambito,
                    "partido": partido,
                    "dep_ubigeo": dep_ubigeo,
                    "porcentaje_votos_emitidos": p.get("porcentajeVotosEmitidos"),
                    "porcentaje_votos_validos": p.get("porcentajeVotosValidos"),
                    "total_votos_validos": p.get("totalVotosValidos"),
                    "color_partido": PARTY_COLOR[partido],
                }
            )

    df = pd.DataFrame(rows)
    return df


# df = build_table(base_dir=BASE_DIR)
# df.to_csv(OUTPUT_DIR.parent.parent / "last_results.csv")
df = pd.read_csv(OUTPUT_DIR.parent.parent / "last_results.csv")

# ---------------------------------------------------------------------------
# Paso 2: descargar / filtrar geometrías por distrito
# ---------------------------------------------------------------------------


def fetch_province_geojson(prov_ubigeo: str, cache_dir: Path = CACHE_DIR, type=1):
    cache_file = cache_dir / f"ambito={type}" / f"{prov_ubigeo}.geojson"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    if cache_file.exists():
        with open(cache_file, encoding="utf-8") as fh:
            return json.load(fh)

    type = "provincias" if type == 1 else "continentes"
    url = GEO_PROVINCIA_BASE_URL.format(prov_ubigeo=prov_ubigeo, type=type)
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=3)
    resp.raise_for_status()
    data = resp.json()

    with open(cache_file, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)

    time.sleep(SLEEP_BETWEEN_REQUESTS)
    return data


for type in [2, 1]:
    ref = "prov_ubigeo"
    if type == 2:
        ref = "dep_ubigeo"
    prov = df.query("ambito==@type")[ref].astype(str).str.zfill(6).unique().tolist()
    if type == 1:
        prov = ["120100", "070900", "170100"]
    # print(prov)

    for p in tqdm.tqdm(prov, desc=str(type)):
        try:
            g = fetch_province_geojson(p, type=type)
        except:
            print(p)
            pass
# fetch_province_geojson("910300", type=2)

# https://resultadosegundavuelta.onpe.gob.pe/assets/lib/amcharts5/geodata/json/continentes/930000.json
