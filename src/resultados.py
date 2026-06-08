import asyncio

from rich import print

from src.api import get


async def get_resultados_distrito(
    ambito: int,
    dep: str,
    prov: str,
    dist: str,
):
    params = {
        "idEleccion": 10,
        "tipoFiltro": "ubigeo_nivel_03",
        "idAmbitoGeografico": ambito,
        "idUbigeoDepartamento": dep,
        "idUbigeoProvincia": prov,
        "idUbigeoDistrito": dist,
    }

    totales = await get(
        "/resumen-general/totales",
        params,
    )

    participantes = await get(
        "/resumen-general/participantes",
        params,
    )

    return {
        "totales": totales,
        "participantes": participantes,
    }


async def main():
    result = await get_resultados_distrito(
        ambito=1, dep="030000", dist="030302", prov="030300"
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
