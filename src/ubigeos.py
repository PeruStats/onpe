import asyncio

from rich import print

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


async def main():
    departamentos = await get_departamentos()
    print(departamentos)


if __name__ == "__main__":
    asyncio.run(main())
