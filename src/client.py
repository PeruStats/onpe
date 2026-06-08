# src.clien.py
import httpx

from src.constants import BASE_URL, HEADERS


def make_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers=HEADERS,
        timeout=httpx.Timeout(10.0, connect=5.0),
        limits=httpx.Limits(max_connections=30, max_keepalive_connections=20),
    )
