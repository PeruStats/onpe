import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from azure.storage.blob import BlobServiceClient
from dotenv import find_dotenv, load_dotenv
from tqdm import tqdm

load_dotenv(find_dotenv())

conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
container = os.environ.get("AZURE_STORAGE_CONTAINER", "resultados")

client = BlobServiceClient.from_connection_string(conn_str)
container_client = client.get_container_client(container)


def upload_file(file: Path):
    blob_name = file.relative_to(Path("data")).as_posix()

    blob_client = container_client.get_blob_client(blob_name)

    with open(file, "rb") as f:
        blob_client.upload_blob(f, max_concurrency=4)


def upload_snapshot(base_path: Path):
    prefix = base_path.relative_to(Path("data")).as_posix()
    existing_blobs = {
        blob.name for blob in container_client.list_blobs(name_starts_with=prefix)
    }

    archivos = [
        f
        for f in base_path.rglob("*.json")
        if f.relative_to(Path("data")).as_posix()
        not in existing_blobs  # <- filtro aquí
    ]

    if not archivos:
        print(f"{base_path.relative_to(Path('data'))} - subido")
        return

    with ThreadPoolExecutor(max_workers=32) as executor:
        list(tqdm(executor.map(upload_file, archivos), total=len(archivos)))


if __name__ == "__main__":
    dir_path = Path("data") / "resultados"

    for snapshot in list(dir_path.iterdir())[::-1]:
        upload_snapshot(snapshot)
