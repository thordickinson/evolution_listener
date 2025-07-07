import os
import json
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

BASE_MEDIA_PATH = "/var/lib/harmony/media"

MIMETYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "application/msword": ".doc",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.ms-powerpoint": ".ppt",
}


def save_media_in_folder(url: str, account_id: str, chat_id: str, message_id: str, mimetype: Optional[str] = None) -> str:
    """
    Descarga un archivo desde la URL y lo guarda en:
      /base/account_id/chat_id/message_id/
    con archivo + metadata.json

    Devuelve la ruta al directorio del mensaje.
    """
    target_dir = os.path.join(BASE_MEDIA_PATH, account_id, chat_id, message_id)
    os.makedirs(target_dir, exist_ok=True)

    ext = None if mimetype is None else MIMETYPE_EXTENSIONS.get(mimetype, "")
    if not ext:
        logger.warning(f"Mimetype desconocido: {mimetype}. Usando extensión .bin")
        ext = ".bin"

    filename = f"file{ext}"
    filepath = os.path.join(target_dir, filename)

    resp = requests.get(url, stream=True, timeout=30)
    if resp.status_code != 200:
        raise Exception(f"Error descargando archivo: {resp.status_code}")

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(1024):
            f.write(chunk)

    # escribir metadata
    metadata = {
        "mimetype": mimetype,
        "size": os.path.getsize(filepath),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "original_name": filename
    }

    with open(os.path.join(target_dir, "metadata.json"), "w") as meta_file:
        json.dump(metadata, meta_file, indent=2)

    logger.info(f"Archivo y metadata guardados en: {target_dir}")
    return target_dir
