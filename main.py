import json
import os
from base_class import ValidationPortalPDPReports
import logging
from dotenv import load_dotenv

from telegram_bot import TelegramBot

# Inicialización del logger
logger = logging.getLogger(__name__)

if __name__ == "__main__":
  # Cargar variables de entorno desde el archivo .env
  load_dotenv()

  info_portal = {
    "url_portal_pdp": "https://ftpayment.co/FTAdmon_Payment-web/login.xhtml",
    "chat_id_telegram": os.getenv("CHAT_ID_YOINER", ""),
    "telegram_bot": TelegramBot(os.getenv("TOKEN_BOT_TELEGRAM", ""))
  }
  task = ValidationPortalPDPReports(
    headless=False, info_portal=info_portal, screenshot_dir="./screenshots", max_wait=60 * 1000)

  print(json.dumps(task.run(), indent=2))
