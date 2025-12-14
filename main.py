import json
from base_class import ValidationPortalPDPReports
import logging

# Inicialización del logger
logger = logging.getLogger(__name__)

if __name__ == "__main__":
  info_portal = {
    "url_portal_pdp": "https://ftpayment.co/FTAdmon_Payment-web/login.xhtml",
  }
  task = ValidationPortalPDPReports(
    headless=False, info_portal=info_portal, screenshot_dir="./screenshots", max_wait=60 * 1000)

  print(json.dumps(task.run(), indent=2))
