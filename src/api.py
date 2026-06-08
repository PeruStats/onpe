# src.api
# src/api.py
# async def get(client: httpx.AsyncClient, endpoint: str, params: dict):
#     response = await client.get(endpoint, params=params)
#     # Ver qué devuelve realmente
#     if response.status_code != 200:
#         raise ValueError(f"HTTP {response.status_code} en {endpoint}")
#     text = response.text.strip()
#     if not text:
#         raise ValueError(f"Respuesta vacía (body='') en {endpoint} | params={params}")
#     try:
#         data = response.json()
#     except Exception:
#         # Muestra los primeros 200 chars del body para diagnosticar
#         raise ValueError(f"JSON inválido en {endpoint}: {text[:200]!r}")
#     return data.get("data")
# src/api.py
# async def get(client: httpx.AsyncClient, endpoint: str, params: dict):
#     response = await client.get(endpoint, params=params)
#     response.raise_for_status()
#     text = response.text.strip()
#     if not text or text in ("null", "{}"):
#         return None  # distrito sin datos — no es un error
#     return response.json().get("data")
# import asyncio

# import httpx

# MAX_RETRIES = 4
# BASE_BACKOFF = 1.0  # segundos


# async def get(client: httpx.AsyncClient, endpoint: str, params: dict):
#     last_error = None

#     for attempt in range(MAX_RETRIES):
#         try:
#             response = await client.get(endpoint, params=params)
#             response.raise_for_status()

#             text = response.text.strip()

#             # Servidor devolvió HTML o body vacío — retry
#             if not text or text.startswith("<"):
#                 raise ValueError(
#                     f"respuesta no-JSON (intento {attempt + 1}): {text[:80]!r}"
#                 )

#             data = response.json()
#             return data.get("data")

#         except (ValueError, httpx.HTTPStatusError, httpx.ReadTimeout) as e:
#             last_error = e
#             wait = BASE_BACKOFF * (2**attempt)  # 1s, 2s, 4s, 8s
#             await asyncio.sleep(wait)

#     # Agotó los reintentos — propaga para que process_distrito lo logguee
#     raise RuntimeError(f"Fallo tras {MAX_RETRIES} intentos en {endpoint}: {last_error}")

import asyncio

import httpx

MAX_RETRIES = 5
BACKOFF_JSON_ERROR = 2.0
BACKOFF_HTML = 15.0


async def get(client: httpx.AsyncClient, endpoint: str, params: dict):
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()

            text = response.text.strip()

            if not text:
                wait = BACKOFF_JSON_ERROR * (2**attempt)
                await asyncio.sleep(wait)
                last_error = "body vacío"
                continue

            if text.startswith("<"):
                jitter = asyncio.get_event_loop().time() % 3.0
                wait = BACKOFF_HTML * (attempt + 1) + jitter
                await asyncio.sleep(wait)
                last_error = f"HTML recibido (intento {attempt + 1})"
                continue

            return response.json().get("data")

        except (httpx.ReadTimeout, httpx.ConnectError) as e:
            wait = BACKOFF_JSON_ERROR * (2**attempt)
            await asyncio.sleep(wait)
            last_error = str(e)

        except httpx.HTTPStatusError as e:
            last_error = str(e)
            break

    raise RuntimeError(f"Fallo tras {MAX_RETRIES} intentos en {endpoint}: {last_error}")
