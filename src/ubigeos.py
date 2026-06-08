import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.api import get


async def get_departamentos(ambito=1):
    return await get(
        "/ubigeos/departamentos",
        {
            "idEleccion": 10,
            "idAmbitoGeografico": ambito,
        },
    )


async def get_provincias(ambito=1, ubigeo_dep="010000"):
    return await get(
        "/ubigeos/provincias",
        {
            "idEleccion": 10,
            "idAmbitoGeografico": ambito,
            "idUbigeoDepartamento": ubigeo_dep,
        },
    )


async def get_distritos(ambito=1, ubigeo_prov="010300"):
    return await get(
        "/ubigeos/distritos",
        {
            "idEleccion": 10,
            "idAmbitoGeografico": ambito,
            "idUbigeoProvincia": ubigeo_prov,
        },
    )


async def main_ubigeos():

    snapshot = datetime.now().strftime("%Y%m%d_%H%M%S")

    base_path = Path("data") / "ubigeos" / f"snapshot={snapshot}"

    for amb in [1, 2]:
        departamentos = await get_departamentos(amb) or []

        for dep in departamentos:
            dep_name = dep["nombre"]
            dep_ubigeo = dep["ubigeo"]

            provincias = (
                await get_provincias(
                    amb,
                    dep_ubigeo,
                )
                or []
            )

            for prov in provincias:
                prov_name = prov["nombre"]
                prov_ubigeo = prov["ubigeo"]

                distritos = (
                    await get_distritos(
                        amb,
                        prov_ubigeo,
                    )
                    or []
                )

                distritos_in_prov = [
                    {
                        "ambito": amb,
                        "dep_name": dep_name,
                        "dep_ubigeo": dep_ubigeo,
                        "prov_name": prov_name,
                        "prov_ubigeo": prov_ubigeo,
                        **dist,
                    }
                    for dist in distritos
                ]

                full_path = (
                    base_path
                    / f"ambito={amb}"
                    / f"dep={dep_ubigeo}"
                    / f"prov={prov_ubigeo}.json"
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
                        distritos_in_prov,
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )


if __name__ == "__main__":
    asyncio.run(main_ubigeos())
