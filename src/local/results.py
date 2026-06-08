import asyncio
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich import print
from tqdm import tqdm

from src.resultados import get_resultados_distrito


def load_ubigeos(snapshot_dir: str):

    registros = []

    for file in Path(snapshot_dir).rglob("*.json"):
        with open(file, encoding="utf-8") as f:
            registros.extend(json.load(f))
    r = pd.DataFrame(registros).drop_duplicates().to_dict("records")
    print(r[:3])
    return r


def save_resultado(
    result,
    base_path,
    ambito,
    dep,
    prov,
    dist,
):

    full_path = (
        base_path
        / f"ambito={ambito}"
        / f"dep={dep}"
        / f"prov={prov}"
        / f"dist={dist}.json"
    )

    full_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        full_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2,
        )


async def process_distrito(
    reg,
    base_path,
):

    ambito = reg["ambito"]
    dep = reg["dep_ubigeo"]
    prov = reg["prov_ubigeo"]
    dist = reg["ubigeo"]

    try:
        await asyncio.sleep(0.4)
        result = await get_resultados_distrito(
            ambito=ambito,
            dep=dep,
            prov=prov,
            dist=dist,
        )

        save_resultado(
            result,
            base_path,
            ambito,
            dep,
            prov,
            dist,
        )

    except Exception as e:
        print(f"Error en {dep}-{prov}-{dist}: {e}")


async def get_data(snapshot_dir: str = "data/ubigeos"):

    snapshot = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_path = Path("data") / "resultados" / f"snapshot={snapshot}"

    registros = load_ubigeos(snapshot_dir)

    for reg in tqdm(registros):
        await process_distrito(
            reg,
            base_path,
        )


asyncio.run(get_data())
