import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx
import pandas as pd
from rich import print
from tqdm.asyncio import tqdm_asyncio

from src.client import make_client
from src.resultados import get_resultados_distrito

CONCURRENCY = 5


def load_ubigeos():

    # leer la tabla de databricks
    data = pd.read_csv(Path("data") / "pendientes" / "pendientes_onpe.csv", dtype=str)
    return data.drop_duplicates().to_dict("records")


def save_resultado(result, base_path, ambito, dep, prov, dist):
    full_path = (
        base_path
        / f"ambito={ambito}"
        / f"dep={dep}"
        / f"prov={prov}"
        / f"dist={dist}.json"
    )
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


async def process_distrito(sem, client, reg, base_path):
    async with sem:
        ambito = reg["ambito"]
        dep = reg["dep_ubigeo"]
        prov = reg["prov_ubigeo"]
        dist = reg["ubigeo"]
        try:
            result = await get_resultados_distrito(
                client=client,
                ambito=ambito,
                dep=dep,
                prov=prov,
                dist=dist,
            )
            result["metadata_loc"] = reg
            if result["totales"] is None and result["participantes"] is None:
                return
            # result["metadata_loc"]= reg
            save_resultado(result, base_path, ambito, dep, prov, dist)
        except httpx.ReadTimeout:
            print(f"[yellow]Timeout[/yellow] {dep}-{prov}-{dist} — reintentando...")
            # opcional: poner en una cola de reintentos
        except Exception as e:
            print(f"[red]Error[/red] {dep}-{prov}-{dist}: {e}")


async def get_data(snapshot_dir: str = "data/ubigeos"):
    snapshot = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = Path("data") / "resultados" / f"snapshot={snapshot}"
    registros = load_ubigeos()

    sem = asyncio.Semaphore(CONCURRENCY)

    async with make_client() as client:
        tasks = [process_distrito(sem, client, reg, base_path) for reg in registros]
        await tqdm_asyncio.gather(*tasks, desc="Distritos")

    # upload_snapshot(base_path)


# regs = load_ubigeos()
# reg = regs[2]
# print(reg)

asyncio.run(get_data())
