from dotenv import load_dotenv
# Cargar .env
load_dotenv()

import logging
from fastapi import FastAPI
from media_downloader import save_media_from_event
from db import add_message
from config import load_config, is_conversation_allowed, should_log_ignored, should_log_accepted



# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Inicializar FastAPI
app = FastAPI()

# Cargar configuración de filtros
CONFIG = load_config("config.yaml")


@app.get("/api/status")
def read_status():
    """
    Devuelve el estado de la API.
    """
    return {"status": "up"}

# … código anterior

@app.post("/api/messages/handle")
async def handle_message(data: dict):
    """
    Recibe y procesa eventos enviados al endpoint.
    Filtra por account_id y chat_id según la configuración.
    """
    try:
        account_id = data.get("sender")
        chat_id = data.get("data", {}).get("key", {}).get("remoteJid")
        if not account_id or not chat_id:
            logger.warning(f"Datos incompletos: account_id={account_id}, chat_id={chat_id}")
            return {"error": "account_id o chat_id faltantes"}

        if not is_conversation_allowed(account_id, chat_id):
            if should_log_ignored():
                logger.info(f"Ignorado: account={account_id}, chat={chat_id}")
            return {"status": "ignored", "reason": "chat_id not allowed"}

        if should_log_accepted():
            logger.info(f"Aceptado: account={account_id}, chat={chat_id}")

        save_media_from_event(data)

        await add_message(data)
        return {"status": "ok"}

    except Exception as e:
        logger.exception("Error procesando el mensaje")
        return {"error": str(e), "message": "Invalid data format"}
