# utils.py
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def ensure_directories(*paths: str) -> None:
    """Asegura que los directorios existen."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def load_cache(path: str) -> Optional[Any]:
    """Carga datos desde caché."""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_cache(path: str, data: Any) -> None:
    """Guarda datos en caché."""
    ensure_directories(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_bronze_path(
    ambito: int,
    ubigeo_type: str,
    name: str,
    sub_type: Optional[str] = None,
    sub_name: Optional[str] = None,
) -> str:
    """
    Construye la ruta según la estructura bronze.

    Ejemplos:
    - ubigeos/ingestion_date=2026-06-07/ambito=1/departamento=LIMA/provincias.json
    - resultados/snapshot=2026-06-07T20-00-00/ambito=1/departamento=JUNIN/provincia=HUANCAYO/120101.json
    """
    ingestion_date = datetime.now().strftime("%Y-%m-%d")

    if ubigeo_type == "ubigeos":
        base_path = f"./bronze/ubigeos/ingestion_date={ingestion_date}/ambito={ambito}"

        if sub_type and sub_name:
            return f"{base_path}/{sub_type}={sub_name}/{name}.json"
        return f"{base_path}/{name}.json"

    elif ubigeo_type == "resultados":
        snapshot = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        base_path = f"./bronze/resultados/snapshot={snapshot}/ambito={ambito}"

        if sub_type and sub_name:
            return f"{base_path}/{sub_type}={sub_name}/{name}.json"
        return f"{base_path}/{name}.json"

    return f"./bronze/{ubigeo_type}/{name}.json"


def parse_response(
    data: List[dict], suffix: str = "dep", add_dict: Dict = None
) -> List[dict]:
    """Parsea la respuesta de la API al formato deseado."""
    if add_dict is None:
        add_dict = {}

    return [
        {
            f"ubigeo_{suffix}": item.get("ubigeo"),
            f"name_{suffix}": item.get("nombre"),
            **add_dict,
        }
        for item in data
    ]
