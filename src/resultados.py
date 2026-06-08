import asyncio

from rich import print

from src.api import get
from src.client import make_client


async def get_resultados_distrito(client, ambito, dep, prov, dist):
    params = {
        "idEleccion": 10,
        "tipoFiltro": "ubigeo_nivel_03",
        "idAmbitoGeografico": ambito,
        "idUbigeoDepartamento": dep,
        "idUbigeoProvincia": prov,
        "idUbigeoDistrito": dist,
    }
    totales = await get(client, "/resumen-general/totales", params)
    # print(totales)
    participantes = await get(client, "/resumen-general/participantes", params)
    return {"totales": totales, "participantes": participantes}


async def main():
    client = make_client()
    result = await get_resultados_distrito(
        client=client, ambito=1, dep="030000", dist="030302", prov="030300"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
