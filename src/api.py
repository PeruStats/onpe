from src.client import client


async def get(endpoint: str, params: dict):
    response = await client.get(endpoint, params=params)
    response.raise_for_status()

    return response.json().get("data")
