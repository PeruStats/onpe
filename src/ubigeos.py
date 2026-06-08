import asyncio

import httpx
from rich import print

from src.constants import BASE_URL, HEADERS


async def get(url, params):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=HEADERS)

        if response.status_code == 200:
            data = response.json().get("data")
            return data
        return None


async def get_departamentos(ambito=1):
    url = f"{BASE_URL}/ubigeos/departamentos"
    params = {"idEleccion": "10", "idAmbitoGeografico": ambito}
    data = await get(url, params=params)
    return data


async def get_provincias(ambito=1, ubigeo_dep="010000"):
    url = f"{BASE_URL}/ubigeos/provincias"
    params = {
        "idEleccion": "10",
        "idAmbitoGeografico": ambito,
        "idUbigeoDepartamento": ubigeo_dep,
    }
    data = await get(url, params=params)
    return data


async def get_distritos(ambito, ubigeo_dep, ubigeo_prov):
    url = f"{BASE_URL}/ubigeos/distritos"  # CORREGIDO: antes decía provincias
    params = {
        "idEleccion": "10",
        "idAmbitoGeografico": ambito,
        "idUbigeoDepartamento": ubigeo_dep,
        "idUbigeoProvincia": ubigeo_prov,
    }
    data = await get(url, params=params)
    print(data)
    return data


async def get_resultados_dist(ambito, dep, prov, dist):
    data = {
        "idEleccion": 10,
        "tipoFiltro": "ubigeo_nivel_03",
        "idAmbitoGeografico": ambito,
        "idUbigeoDepartamento": dep,
        "idUbigeoProvincia": prov,
        "idUbigeoDistrito": dist,
    }
    url_totales = f"{BASE_URL}/resumen-general/totales"
    url_candidatos = f"{BASE_URL}/resumen-general/participantes"
    data_totales = await get(url_totales, params=data)
    data_candidatos = await get(url_candidatos, params=data)
    print(data_totales)
    print(data_candidatos)


async def main_ubigeos():
    # obtiene los ubigeos, pero tiene que tener la metadata de los loops mas arrriba para poder extraer
    # informacion de resultados y totales  y guardar a nivel de provincia.json
    # output prefereido para un cloud storage
    # ubigeos/snapshot=timestamp/ambito=1,2/departamento=ubigeo_dep/provincia_{ubigeo_provincia}.json
    for amb in [1, 2]:  # 1 para peru, 2 para extranjero
        departamentos = await get_departamentos(amb)

        # Crear tareas para TODAS las provincias en paralelo
        tareas_provincias = [
            get_provincias(amb, dep.get("ubigeo")) for dep in departamentos
        ]
        todas_provincias = await asyncio.gather(*tareas_provincias)

        # Crear tareas para TODOS los distritos en paralelo
        tareas_distritos = []
        for dep, provincias in zip(departamentos, todas_provincias):
            for prov in provincias:
                tareas_distritos.append(
                    get_distritos(amb, dep.get("ubigeo"), prov.get("ubigeo"))
                )

        todos_distritos = await asyncio.gather(*tareas_distritos)


async def main_resultados():
    # primero se leera todos los snapshot, luego se obtendra los ubigeos_unicos
    # luego esa tabla se exportara a un 'silver'
    # luego se lee la tabla y fila por fila (httx) se hace la peticion de la api para los resultados y totales y se guarda en el storage
    # output preferido para el cloud storge
    # resultados_candidatos/snapshotf=timestamp/ambito=1,2/departamento=ubigeo_dep/provincia=ubigeo_prov/distrito=ubigeo_dist.json
    # totales_actas/snapshotf=timestamp/ambito=1,2/departamento=ubigeo_dep/provincia=ubigeo_prov/distrito=ubigeo_dist.json
    # for results
    # luego se lee todos los snapshot json se procesa y se guarda en un silver usando el timestamp para filstros de evolucion
    # de esta tabla se toma el resultado por el ubigeo distrital y el tiempo mas actual y se exporta las tablas gold, para el uso de los dashboards
    # luego compartir como delta share para el uso del endopoint
    pass


if __name__ == "__main__":
    import asyncio
    import time

    # json de los ubigeos, solo se reemplaza por 0 los numeros mas especificos
    #     {'ubigeo': '940401', 'nombre': 'AMBERES'},
    # {'ubigeo': '940402', 'nombre': 'BRUSELAS'},
    # {'ubigeo': '940403', 'nombre': 'GANTE'},
    # {'ubigeo': '940404', 'nombre': 'LIEJA'}

    def benchmark(name, fn):
        start = time.perf_counter()
        asyncio.run(fn())
        elapsed = time.perf_counter() - start

        print(f"{name}: {elapsed:.2f}s")
        return elapsed

    # secuencial = benchmark("Secuencial", main)
    paralelo = benchmark("Paralelo", main_ubigeos)  # 6 SEGUNDOS

    asyncio.run(get_resultados_dist(1, "010000", "010200", "010202"))

    # print(
    #     f"\nSpeedup: {secuencial / paralelo:.2f}x" if paralelo > 0 else "\nSpeedup: N/A"
    # )
