from pathlib import Path

import geopandas as gpd
import pandas as pd
from rich import print

DATA = Path("data")
CACHE_DIR = DATA / "last_review"

for ambito in [1, 2]:
    path = CACHE_DIR / "geometry" / "prov" / f"ambito={ambito}"

    files = sorted(path.rglob("*.geojson"))
    gdfs = []

    for f in files:
        try:
            gdfs.append(gpd.read_file(f))
        except Exception as e:
            print(f"Error leyendo {f}")
            print(e)

    result = gpd.GeoDataFrame(
        pd.concat(gdfs, ignore_index=True),
        crs=gdfs[0].crs,
    )

    # result = gpd.GeoDataFrame(
    #     pd.concat((gpd.read_file(f) for f in files), ignore_index=True),
    #     crs=gpd.read_file(files[0]).crs,
    # )

    out_file = CACHE_DIR / f"{ambito}.geojson"
    result.to_file(out_file, driver="GeoJSON")
