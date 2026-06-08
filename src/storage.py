import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def upload_snapshot(base_path: Path):
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container = os.environ.get("AZURE_STORAGE_CONTAINER", "resultados")

    client = BlobServiceClient.from_connection_string(conn_str)
    container_client = client.get_container_client(container)

    archivos = list(base_path.rglob("*.json"))
    print(f"Subiendo {len(archivos)} archivos a Azure Blob Storage...")

    for file in archivos:
        # Mantiene la estructura de carpetas como blob name
        blob_name = file.relative_to(Path("data")).as_posix()
        with open(file, "rb") as f:
            container_client.upload_blob(
                name=blob_name,
                data=f,
                overwrite=True,
            )

    print(f"✅ Subida completa → container '{container}'")
