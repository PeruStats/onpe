import httpx

from src.constants import BASE_URL, HEADERS

client = httpx.AsyncClient(
    base_url=BASE_URL,
    headers=HEADERS,
    timeout=1.5,
)
