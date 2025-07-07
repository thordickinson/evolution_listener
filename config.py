import yaml
import logging

logger = logging.getLogger(__name__)

CONFIG = {}


def load_config(path: str = "config.yaml"):
    """
    Carga el YAML en el dict global CONFIG.
    """
    global CONFIG
    with open(path, "r") as f:
        CONFIG.clear()
        CONFIG.update(yaml.safe_load(f) or {})
    logger.info(f"Configuración cargada: {CONFIG}")
    return CONFIG


def is_conversation_allowed(account_id: str, chat_id: str) -> bool:
    """
    Devuelve True si el chat_id está permitido para el account_id según el YAML.
    """
    account_filters = CONFIG.get("filters", {}).get(account_id)
    if not account_filters:
        logger.warning(f"Account {account_id} no tiene filtros definidos")
        return False
    allowed = account_filters.get("conversations", [])
    return chat_id in allowed


def should_log_ignored() -> bool:
    """
    Devuelve True si se debe loggear en consola los chats ignorados.
    """
    return CONFIG.get("logging", {}).get("log_ignored_chats", False)

def should_log_accepted() -> bool:
    """
    Devuelve True si se deben loggear en consola los chats aceptados.
    """
    return CONFIG.get("logging", {}).get("log_accepted_chats", False)

