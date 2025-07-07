import os
import json
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# lee la variable de entorno, o usa la ruta por defecto
BASE_MEDIA_PATH = os.environ.get("HARMONY_MEDIA_PATH", "/var/lib/harmony/media")

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


def __download_media(url: str, account_id: str, chat_id: str, message_id: str, mimetype: Optional[str] = None) -> str:
    """
    Descarga un archivo desde la URL y lo guarda en:
      BASE_MEDIA_PATH/account_id/chat_id/message_id/
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



def save_media_from_event(event: dict) -> Optional[str]:
    """
    Extrae la URL, account_id, chat_id y message_id de un evento
    y descarga el archivo en BASE_MEDIA_PATH/account_id/chat_id/message_id.ext.

    Devuelve la ruta completa del archivo guardado o None si no hay media.
    """
    try:
        data = event.get("data", {})
        message = data.get("message", {})

        # detecta el tipo de mensaje con media
        media_message = None
        mimetype = None
        for media_type in ["imageMessage", "videoMessage", "documentMessage"]:
            if media_type in message:
                media_message = message[media_type]
                break

        if not media_message or "url" not in media_message:
            logger.info("No se encontró contenido multimedia con URL en el evento")
            return None

        url = media_message["url"]
        mimetype = media_message.get("mimetype")
        message_id = data["key"]["id"]
        account_id = event["sender"]
        chat_id = data["key"]["remoteJid"]

        return __download_media(
            url=url,
            account_id=account_id,
            chat_id=chat_id,
            message_id=message_id,
            mimetype=mimetype,
        )

    except Exception as e:
        logger.exception(f"Error al procesar media del evento: {e}")
        return None
