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
