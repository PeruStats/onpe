# constants.py
ID_ELECCION = 10

BASE_URL = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend"

HEADERS = {
    "accept": "*/*",
    "accept-language": "es,en;q=0.9,en-US;q=0.8,ca;q=0.7,zh-CN;q=0.6,zh;q=0.5",
    "content-type": "application/json",
    "priority": "u=1, i",
    "referer": "https://resultadoelectoral.onpe.gob.pe/main/resumen",
    "sec-ch-ua": '"Opera";v="131", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 OPR/131.0.0.0",
}


CACHE_DIR = "./data/onpe/cache"
OUTPUT_DIR = "./data/onpe"
