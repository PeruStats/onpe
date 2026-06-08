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
    #     {
    #     'totales': {
    #         'actasContabilizadas': 0.0,
    #         'contabilizadas': 0,
    #         'totalActas': 23,
    #         'participacionCiudadana': 0.0,
    #         'actasEnviadasJee': 0.0,
    #         'enviadasJee': 0,
    #         'actasPendientesJee': 100.0,
    #         'pendientesJee': 23,
    #         'fechaActualizacion': 1780881723531,
    #         'idUbigeoDepartamento': 30000,
    #         'idUbigeoProvincia': 30300,
    #         'idUbigeoDistrito': 30302,
    #         'idUbigeoDistritoElectoral': None,
    #         'totalVotosEmitidos': 0,
    #         'totalVotosValidos': 0,
    #         'porcentajeVotosEmitidos': 0,
    #         'porcentajeVotosValidos': 0
    #     },
    #     'participantes': [
    #         {
    #             'nombreAgrupacionPolitica': 'FUERZA POPULAR',
    #             'codigoAgrupacionPolitica': 8,
    #             'nombreCandidato': 'KEIKO SOFIA FUJIMORI HIGUCHI',
    #             'dniCandidato': '10001088',
    #             'totalVotosValidos': 0,
    #             'porcentajeVotosValidos': 0.0,
    #             'porcentajeVotosEmitidos': 0.0
    #         },
    #         {
    #             'nombreAgrupacionPolitica': 'JUNTOS POR EL PERÚ',
    #             'codigoAgrupacionPolitica': 10,
    #             'nombreCandidato': 'ROBERTO HELBERT SANCHEZ PALOMINO',
    #             'dniCandidato': '16002918',
    #             'totalVotosValidos': 0,
    #             'porcentajeVotosValidos': 0.0,
    #             'porcentajeVotosEmitidos': 0.0
    #         }
    #     ]
    # }


if __name__ == "__main__":
    asyncio.run(main())
