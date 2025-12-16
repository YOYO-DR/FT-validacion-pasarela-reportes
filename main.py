import json
import os
from base_class import ValidationPortalPDPReports
import logging
from dotenv import load_dotenv

from telegram_bot import TelegramBot

# Configuración global del logger
logging.basicConfig(
  level=logging.INFO, format="%(levelname)s:%(name)s:%(funcName)s:%(message)s"
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
  # Cargar variables de entorno desde el archivo .env
  load_dotenv()

  info_portal = {
    "url_portal_pdp": "https://ftpayment.co/FTAdmon_Payment-web/login.xhtml",
    "chat_ids_telegram": os.getenv("CHAT_ID_YOINER", "").split(","),
    "telegram_bot": TelegramBot(os.getenv("TOKEN_BOT_TELEGRAM", ""))
  }
  # TODO: implementar el SessionManager para varias pestañas con esto https://chatgpt.com/c/69402eba-98d8-832d-8b1f-d8ecd8a2fc7c
  task = ValidationPortalPDPReports(
    headless=False, info_portal=info_portal, screenshot_dir="./screenshots", max_wait=120 * 1000)

  print(json.dumps(task.run(), indent=2))
