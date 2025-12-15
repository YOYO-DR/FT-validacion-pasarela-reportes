import logging
import os
import re
from datetime import datetime
from time import sleep
from functions import delete_files_dir_time
from telegram_bot import TelegramBot
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError, expect
from constans import IGNORE_COMERCIOS_VALIDATIONS, MAX_VALUES_PER_PAGE, SELECTOR_REPORT_CONSULT, SELECTORS_REPORT_CONSULT_OPTIONS, SELECTOR_WAIT_LOADING, ROWS_TABLE_REPORT_CONSULT

# Configuración global del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseFlowTask:
  """
  Clase base para tareas automatizadas usando Playwright.
  Maneja el ciclo de vida del navegador y la captura de pantallas.
  """

  def __init__(self, headless=False, max_wait=30000, screenshot_dir=None):
    """
    Inicializa los parámetros básicos de la tarea.

    :param headless: Ejecutar navegador en modo headless (sin UI)
    :param max_wait: Tiempo máximo de espera en milisegundos
    :param task_id: Identificador único de la tarea
    """
    self.headless = headless
    self.max_wait = max_wait
    self.screenshot_dir = screenshot_dir
    self.screenshot_path = None
    self.browser = None
    self.context = None
    self.page = None
    self.playwright = None

  def launch_page(self, url: str, context=None):
    """
    Navega a la URL especificada y espera a que la página se cargue completamente.

    :param url: URL a la que navegar
    Lanza una excepción si ocurre un error durante la navegación.
    """
    logger.info(f"Navegando a la URL: {url}")
    try:
      if not context:
        context = self.browser.new_context(
            viewport={"width": 1920, "height": 930})

      self.page = context.new_page()
      self.page.goto(url, timeout=self.max_wait, wait_until="load")
    except PlaywrightTimeoutError:
      logger.exception(f"Tiempo de espera agotado al navegar a: {url}")
      raise
    except PlaywrightError:
      logger.exception(f"Error de Playwright al navegar a: {url}")
      raise
    except Exception:
      logger.exception(f"Error inesperado al navegar a: {url}")
      raise

  def launch_browser(self):
    """
    Inicia el navegador Playwright y configura el contexto de la página.

    Lanza una excepción si ocurre un error durante la inicialización.
    """
    logger.info("Lanzando navegador...")
    try:
      self.playwright = sync_playwright().start()
      self.browser = self.playwright.chromium.launch(headless=self.headless)
    except PlaywrightError:
      logger.exception("Error de Playwright al lanzar el navegador")
      raise
    except Exception:
      logger.exception("Error inesperado al lanzar el navegador")
      raise

  def close_browser(self):
    """
    Cierra correctamente el navegador, el contexto y detiene Playwright.

    Lanza una excepción si ocurre un error durante el cierre.
    """
    logger.info("Cerrando navegador...")
    try:
      if self.context:
        self.context.close()
      if self.browser:
        self.browser.close()
      if self.playwright:
        self.playwright.stop()
    except PlaywrightError:
      logger.exception("Error de Playwright al cerrar el navegador")
      raise
    except Exception:
      logger.exception("Error inesperado al cerrar el navegador")
      raise

  def take_screenshot(self, name_prefix="screenshot", error=False, full_page=True):
    """
    Toma una captura de pantalla de la página actual.

    :param error: Si True, marca la captura como asociada a un error.
    :param name_prefix: Prefijo del nombre del archivo de la captura.
    :return: Ruta absoluta de la captura generada.
    """
    try:
      timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
      status = "error" if error else "success"
      filename = f"{name_prefix}_{status}_{timestamp}.png"
      path = os.path.join(self.screenshot_dir, filename)
      self.page.screenshot(path=path, full_page=full_page)
      return path
    except PlaywrightError:
      logger.exception("Error al tomar la captura de pantalla")
      raise
    except Exception:
      logger.exception("Error inesperado al tomar la captura de pantalla")
      raise

  def click_first_visible_match(self, selector: str, timeout: int = None):
    """
    Hace clic en el primer elemento visible que coincida con el selector dado.

    Args:
        selector (str): Selector CSS.
        timeout (int, optional): Tiempo máximo en milisegundos para el click.

    Raises:
        ValueError: Si no se encuentra un elemento visible.
        PlaywrightError / Exception: Si ocurre un error al hacer click.
    """
    try:
      logger.info(
        f"Buscando elementos que coincidan con el selector: {selector}")
      elements = self.page.query_selector_all(selector)
      logger.info(
        f"{len(elements)} elementos encontrados para el selector: {selector}")

      for el in elements:
        if el.is_visible():
          logger.info("Elemento visible encontrado, haciendo clic...")
          el.click(timeout=timeout or self.max_wait)
          return
      msg = f"No se encontró ningún elemento visible para el selector: {selector}"
      logger.warning(msg)
      raise ValueError(msg)

    except PlaywrightError:
      logger.exception(
        f"Error de Playwright al hacer click en selector visible: {selector}")
      raise
    except Exception:
      logger.exception(
        f"Error inesperado al hacer click en selector visible: {selector}")
      raise

  def wait_loading(self, timeout=60000):
    """
    Espera a que el elemento de carga
    se vuelva invisible.

    Primero espera 0.5 segundos fijos. Luego, sondea hasta que el elemento
    tenga 'display: none;' en su estilo o simplemente no sea visible.
    """
    # 1. Espera fija inicial de medio segundo
    self.page.wait_for_timeout(500)

    # 2. Localiza el elemento de carga
    loading_element = self.page.locator(SELECTOR_WAIT_LOADING)

    # 3. Espera a que el elemento no sea visible (Playwright lo maneja internamente)
    # Playwright esperará hasta que el elemento cumpla la condición o se agote el tiempo de espera.
    expect(loading_element).not_to_be_visible(timeout=timeout)

  def wait_and_validate_visible(self, selector: str, timeout: int = None) -> bool:
    """
    Espera a que un elemento exista y sea visible en la página.
    :param selector: Selector CSS del elemento a esperar.
    :param timeout: Tiempo máximo en milisegundos para esperar.
    :return: El elemento localizado si es visible.
    """
    try:
      logger.info(f"Esperando a que el elemento sea visible: {selector}")
      self.page.wait_for_selector(
        selector, state="attached", timeout=timeout or self.max_wait)
      self.page.wait_for_selector(
        selector, state="visible", timeout=timeout or self.max_wait)
      return True
    except PlaywrightTimeoutError:
      logger.warning(
        f"Tiempo de espera agotado para que el elemento sea visible: {selector}")
      return False

  def run(self):
    """
    Método abstracto que debe ser implementado por cualquier subclase.

    Lanza NotImplementedError si no es sobrescrito.
    """
    raise NotImplementedError(
      "El método run() debe ser implementado en la subclase")


class ValidationPortalPDPReports(BaseFlowTask):
  """
  Clase base para validar el flujo del portal Bancoomeva Estado Cuenta.
  Hereda de BaseFlowTask para manejar el ciclo de vida del navegador y la captura de pantallas.
  """

  def __init__(self, headless=False, max_wait=30000, info_portal=None, screenshot_dir=None):
    """
    Inicializa los parámetros específicos de la tarea de validación.

    :param headless: Ejecutar navegador en modo headless (sin UI)
    :param max_wait: Tiempo máximo de espera en milisegundos
    :param task_id: Identificador único de la tarea
    :param info_portal: Información del portal a validar
    """
    super().__init__(headless, max_wait, screenshot_dir)
    self.info_portal = info_portal
    self.telegram_bot: TelegramBot = info_portal.get("telegram_bot")

  def init_login(self):
    """
    Inicializa el proceso de login en el portal administrativo de la pasarela. Espera el redireccionamiento al index.
    """
    logger.info("Iniciando login en el portal PDP...")
    url_login = self.info_portal.get("url_portal_pdp")
    if not url_login:
      raise ValueError(
        "La URL del portal PDP no está definida en info_portal.")
    # Lanzar el navegador y abrir la página de login
    self.launch_browser()
    self.launch_page(url_login)

    # Esperar a que se redireccione al index después del login, esperar almenos 60 segundos
    self.page.wait_for_url(
      "https://ftpayment.co/FTAdmon_Payment-web/pages/index.xhtml", timeout=60 * 1000)

    # Validar que se haya cargado el elemento principal del portal
    if not self.wait_and_validate_visible(".ui-panel-content h1", timeout=self.max_wait):
      raise Exception("No se pudo cargar el portal PDP después del login.")

    logger.info("Login exitoso y portal PDP cargado.")

  def open_report_view(self, report_name: str):
    """
    Abre la vista de reporte especificada en el portal PDP.

    :param report_name: Nombre del reporte a abrir.
    """
    logger.info(f"Abriendo la vista de reporte: {report_name}")

    # Abrir opcion de reporte específica
    report_option = SELECTORS_REPORT_CONSULT_OPTIONS.get(report_name)
    if not report_option:
      raise ValueError(
        f"El reporte '{report_name}' no está definido en SELECTORS_REPORT_CONSULT_OPTIONS.")

    # Hacer clic en el menú de consulta de reportes
    # Validar si el boton de consulta esta abierto
    button_consult_visible = self.page.locator(SELECTOR_REPORT_CONSULT)
    # Validar si contiene la clase active-menu
    if "active-menu" not in button_consult_visible.get_attribute("class"):
      self.click_first_visible_match(SELECTOR_REPORT_CONSULT)

    self.click_first_visible_match(report_option["selector"])
    # Esperar a que se cargue la URL del reporte
    self.page.wait_for_url(report_option["url"], timeout=self.max_wait)

    # Dar tiempo para que cargue la vista
    sleep(5)

    # Validar que se haya cargado la vista con éxito
    if not self.wait_and_validate_visible(".BigTopic", timeout=self.max_wait):
      raise Exception(f"No se pudo cargar la vista del reporte: {report_name}")

    logger.info(f"Vista del reporte '{report_name}' cargada exitosamente.")

  def exe_consult_and_ext_data(self):
    """
    Ejecuta la consulta del reporte y extrae los datos de la tabla.
    """
    logger.info("Ejecutando consulta del reporte y extrayendo datos...")
    # Max valores por pagina

    # Ejecutar la consulta
    self.click_first_visible_match("button span.fa-search")

    # Esperar a que cargue la tabla de resultados
    logger.info("Esperando a que cargue la tabla de resultados...")
    self.wait_loading()

    # Obtener el número dew filas con el texto del paginador
    paginator_text = self.page.locator(".ui-paginator-current").inner_text()

    # Con una expresión regular extraer el número de filas (1 de 1 (0 registros))
    match = re.search(r'\((\d+)\s+registros\)', paginator_text)
    num_rows = 0
    if match:
      num_rows = int(match.group(1))

    logger.info(f"Número de filas en el reporte: {num_rows}")

    # Calcular el número de páginas
    num_pages = (num_rows + MAX_VALUES_PER_PAGE - 1) // MAX_VALUES_PER_PAGE
    logger.info(f"Número de páginas a procesar: {num_pages}")

    # Poner la paginacion en 22 registros por pagina
    # Obtener elemento del select de paginación
    page_size_select = self.page.locator("[name$='tableDetalle_rppDD']")
    page_size_select.select_option("22")

    # Esperar a que cargue la tabla con el nuevo tamaño de página
    self.wait_loading()

    # Extraer datos de cada página
    all_data = []

    # Tomar foto a las tablas por pagina
    screenshots_table = []

    for page in range(num_pages):
      logger.info(f"Procesando página {page + 1} de {num_pages}...")
      # Validar que la pagina sea la correcta
      conta_pages = self.page.locator(".ui-paginator-pages")
      # Recorrer elemtos a y validar cual tiene la clase ui-state-active
      page_links = conta_pages.locator("a")
      for i in range(page_links.count()):
        link = page_links.nth(i)
        class_attr = link.get_attribute("class") or ""
        if "ui-state-active" in class_attr:
          current_page = int(link.inner_text())
          if current_page != page + 1:
            # Si es diferente, hacer click en el link de la pagina correcta
            target_link = page_links.nth(page)
            target_link.click()
            # Esperar a que cargue la tabla
            self.wait_loading()
          break
      # Obtener elemento de la tabla
      table_locator = self.page.locator(".ui-datatable-tablewrapper table")
      # Tomar captura de pantalla de la tabla
      # En la etiqueta bodi, poner un zoom de 0.6 para que se vea toda la tabla en la captura
      self.page.evaluate("document.body.style.zoom='0.6'")
      screenshot_path = os.path.join(
        self.screenshot_dir, f"table_page_{page + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
      table_locator.screenshot(path=screenshot_path)
      screenshots_table.append(screenshot_path)
      # Restaurar el zoom al 100%
      self.page.evaluate("document.body.style.zoom='1'")
      # Recorrer las filas de la tabla
      rows = table_locator.locator("tbody tr")
      row_count = rows.count()

      for row_index in range(row_count):
        row_data = {}
        row = rows.nth(row_index)
        # Recorrer las columnas definidas en ROWS_TABLE_REPORT_CONSULT
        for col_index, col_name in enumerate(ROWS_TABLE_REPORT_CONSULT):
          cell = row.locator("td").nth(col_index)
          cell_text = cell.inner_text().strip()
          row_data[col_name] = cell_text
        all_data.append(row_data)
    return all_data, screenshots_table

  def validate_failures_vs_approvals(self, data_table: list):
    """
    Valida que no haya más transacciones Fallidas que Aprobadas por comercio.

    :param data_table: Lista de diccionarios con los datos extraídos.
    """
    logger.info(
      "Validando que no haya más transacciones Fallidas que Aprobadas por comercio...")
    comersios_with_issues = []

    for row in data_table:
      comercio = row["Comercio"]
      # Validar si se debe ignorar este comercio
      if comercio in IGNORE_COMERCIOS_VALIDATIONS.get("failures_vs_approvals", []):
        logger.info(f"Ignorando validación para el comercio: {comercio}")
        continue
      aprobadas = int(row["# Aprobadas"].replace(
        ",", "").replace(".", "") or "0")
      fallidas = int(row["# Fallidas"].replace(
        ",", "").replace(".", "") or "0")
      rechazadas = int(row["# Rechazada"].replace(
        ",", "").replace(".", "") or "0")

      if fallidas > aprobadas or rechazadas > aprobadas:
        comersios_with_issues.append(comercio)

    logger.info(
      "Validación exitosa: No hay más transacciones Fallidas que Aprobadas por comercio.")

    return comersios_with_issues

  def validate_state_last_time(self, comercio_name: str, states_to_check: list) -> bool:
    """
    Valida que las transacciones no finales, no finales efectivo y no reportadas
    no hayan tardado más de 60 minutos en resolverse.

    :param comercio: Nombre del comercio a validar.
    """
    # Validar que haya almenos un estado a validar
    if not states_to_check:
      logger.info(
        "No hay estados definidos para validar en validate_state_last_time.")
      return True
    # Crear lsita de estados segun su equivalencia con el select de estados del reporte por fecha
    estados_equivalentes = {
      "# No Finales": "NO FINALES",
      "# No Finales EF": "NO FINALES EFE",
      "# No Reportaadas": "NO REPORTADO"
    }
    # Navegar a la vista de Registro Por Fecha
    self.open_report_view("Registros Por Fecha")

    # Poner el nombre del comercio en mayusculas
    comercio_name_upper = comercio_name.upper()

    # Seleccionar el comercio en el filtro
    # Abrir el dropdown de comercios
    self.click_first_visible_match("[id$='form:txtComercio_label']")

    # Esperar 1 segundo
    sleep(1)

    # Hacer clic en el comercio específico
    self.click_first_visible_match(f"[data-label='{comercio_name_upper}']")

    # Dar una espera de 2 segundos
    sleep(2)

    # Recorrer los estados a validar para cada consulta a ejecutar
    for state in states_to_check:
      state_equiv = estados_equivalentes.get(state)
      if not state_equiv:
        logger.warning(
          f"No se encontró una equivalencia para el estado: {state}")
        continue
      # Seleccionar el estado en el filtro
      # Abrir el dropdown de estados
      self.click_first_visible_match("[id$='form:txtEstado_label']")

      # Hacer clic en el estado específico
      self.click_first_visible_match(f"[data-label='{state_equiv}']")

      # Dar una espera de 1 segundo
      sleep(1)

      # Ejecutar la consulta
      self.click_first_visible_match("button span.fa-search")

      # Esperar a que cargue la tabla de resultados
      self.wait_loading()

      # obtener la cantidad de registros
      paginator_text = self.page.locator(".ui-paginator-current").inner_text()
      match = re.search(r'\((\d+)\s+registros\)', paginator_text)
      num_rows = 0
      if match:
        num_rows = int(match.group(1))
      if num_rows == 0:
        logger.info(
          f"No hay registros para el comercio '{comercio_name}' en el estado '{state_equiv}'.")
        continue

      logger.info(
        f"Validando tiempo de resolución para el comercio '{comercio_name}' en el estado '{state_equiv}'...")

      if num_rows > 7:
        logger.info(
          f"El número de registros ({num_rows}) es mayor a 7, yendo a la última página...")
        # Ir a la última página
        self.click_first_visible_match(
          ".ui-paginator-last[aria-label='Last Page']")

      # Obtener la información de la ultima fila de la tabla
      table_locator = self.page.locator(".ui-datatable-tablewrapper table")

      rows = table_locator.locator("tbody tr")
      # Convertir el row en un diccionario segun las columnas definidas
      row_count = rows.count()
      if row_count == 0:
        logger.info(
          f"No hay registros para el comercio '{comercio_name}' en el estado '{state_equiv}'.")
        continue
      last_row = rows.nth(row_count - 1)
      # Obtener la columna de tiempo transcurrido
      time_elapsed_text = last_row.locator("td").nth(10).inner_text().strip()

      # Convertir a horas y minutos (formato 02:10:14 P.M.)
      # Eliminar puntos de A.M./P.M. para que coincida con %p
      time_elapsed_text = time_elapsed_text.replace(".", "")
      if time_elapsed_text == "":
        # Recorrer la fila para ver si hay un valor en la columna de hora transcurrido
        for i in range(11):
          cell_text = last_row.locator("td").nth(i).inner_text().strip()
          if cell_text != "":
            if "PM" in cell_text or "AM" in cell_text:
              try:
                time_elapsed_text = datetime.strptime(cell_text, "%I:%M:%S %p")
              except Exception:
                logger.warning(
                  f"No se pudo convertir el tiempo transcurrido '{cell_text}' a formato de hora.")
                break
      # Si no se logra validar el tiempo transcurrido, registrar advertencia y continuar
      if time_elapsed_text == "":
        logger.warning(
          f"No se encontró un valor válido de tiempo transcurrido para el comercio '{comercio_name}' en el estado '{state_equiv}'.")
        return True

      ultima_hora = datetime.strptime(time_elapsed_text, "%I:%M:%S %p")

      # Calcular el tiempo transcurrido en minutos desde la ultima hora hasta ahora
      now = datetime.now()
      tiempo_transcurrido = (now - ultima_hora.replace(year=now.year,
                             month=now.month, day=now.day)).total_seconds() / 60

      if tiempo_transcurrido > 60:
        logger.warning(
          f"El comercio '{comercio_name}' tiene transacciones en estado '{state_equiv}' sin resolver por más de 60 minutos.")
        return True

    return False

  def validate_non_final_transactions(self, data_table: list):
    """
    Valida las transacciones no finales/no finales efectivo por comercio.

    :param data_table: Lista de diccionarios con los datos extraídos.
    """
    logger.info(
      "Validando transacciones no finales/no finales efectivo por comercio...")
    comersios_with_issues = []

    for row in data_table:
      comercio_name = row["Comercio"]
      # Obtener la cantidad de no finales y no finales efectivo
      no_finales = int(row["# No Finales"].replace(",", "") or "0")
      no_finales_efectivo = int(row["# No Finales EF"].replace(",", "") or "0")
      no_reported = int(row["# No Reportaadas"].replace(",", "") or "0")

      # Validar si hay mas de 1 transacción no final efectivo
      suma_estados = no_finales + no_finales_efectivo + no_reported
      if suma_estados > 0:
        states_to_check = []
        if no_finales > 0:
          states_to_check.append("# No Finales")
        if no_finales_efectivo > 0:
          states_to_check.append("# No Finales EF")
        if no_reported > 0:
          states_to_check.append("# No Reportaadas")

        if self.validate_state_last_time(comercio_name=comercio_name, states_to_check=states_to_check):
          comersios_with_issues.append(comercio_name)

    if len(comersios_with_issues) == 0:
      logger.info(
        "Validación exitosa: Transacciones no finales/no finales efectivo dentro del tiempo esperado.")
    else:
      logger.warning(
        "Se encontraron comercios con transacciones no finales/no finales efectivo fuera del tiempo esperado.")

    return comersios_with_issues

  def validate_report_data(self, data_table: list):
    """
    Valida la información extraída del reporte.

    :param data_table: Lista de diccionarios con los datos extraídos.
    """
    logger.info("Validando datos extraídos del reporte...")
    if not data_table:
      raise ValueError("No se extrajeron datos del reporte.")

    logger.info(f"Se extrajeron {len(data_table)} filas del reporte.")

    # Variable para armar mensaje de resultados
    message_results = ""
    # 1. Validar que no hayan más transacciones Fallidas/Rechazadas que Aprobadas por comercio
    comercios_issues_fa_ap = self.validate_failures_vs_approvals(data_table)

    # 2. Validar las transacciones no finales, no finales efectivo y no reportadas por comercio
    comercios_issues_non_final = self.validate_non_final_transactions(
      data_table)

    # 3. Armar mensaje de resultados
    # Mensaje de resultados para las falidas vs aprobadas
    if not comercios_issues_fa_ap:
      logger.info(
        "No se encontraron comercios con más transacciones Fallidas/Rechazadas que Aprobadas.")
      message_results += "✅ No se encontraron comercios con más transacciones Fallidas/Rechazadas que Aprobadas.\n"
    else:
      logger.warning(
        "Se encontraron comercios con más transacciones Fallidas/Rechazadas que Aprobadas.")
      message_results += "❌ Comercios con más transacciones Fallidas/Rechazadas que Aprobadas:\n"
      for comercio in comercios_issues_fa_ap:
        message_results += f' - {comercio} \n'

    # Mensaje de resultados para las no finales
    if not comercios_issues_non_final:
      logger.info(
        "No se encontraron comercios con transacciones no finales/no finales efectivo fuera del tiempo esperado.")
      message_results += "✅ No se encontraron comercios con transacciones no finales, no finales efectivo y sin reportar fuera del tiempo esperado.\n"
    else:
      logger.warning(
        "Se encontraron comercios con transacciones no finales/no finales efectivo fuera del tiempo esperado.")
      message_results += "❌ Comercios con transacciones no finales, no finales efectivo y sin reportar fuera del tiempo esperado:\n"
      for comercio in comercios_issues_non_final:
        message_results += f' - {comercio} \n'

    return message_results

  def validate_portal_pdp(self):
    """
    Realiza la validación del portal PDP, reporte monitoreo por estado.
    """

    # Abrir vista de consulta "Monitoreo Por Estado"
    self.open_report_view("Monitoreo Por Estado")

    # Ejecutar consulta del reporte y extraer datos de la tabla
    data_table, screenshots_table = self.exe_consult_and_ext_data()

    # Validar información extraída
    message_validation = self.validate_report_data(data_table)
    if message_validation == "":
      message_validation = "✅ Todas las validaciones del reporte pasaron correctamente. No se encontraron evidencias."

    # Enviar mensaje con resultados por telegram
    logger.info("Validación del reporte completada. Preparando resultados...")
    logger.info("Resultados de la validación:\n" + message_validation)

    # Instaciar el bot de telegram
    chat_id_telegram = self.info_portal.get("chat_id_telegram", "")

    envio = self.telegram_bot.enviar_mensaje_con_archivos(
      chat_id_telegram, message_validation, screenshots_table)
    if envio:
      logger.info("Resultados enviados por Telegram exitosamente.")
    else:
      logger.warning("No se pudieron enviar los resultados por Telegram.")
      # Enviar mensaje simple sin archivos
      message_validation += "\n\n(No se pudieron enviar las capturas de pantalla adjuntas, validar logs.)"
      self.telegram_bot.enviar_mensaje(chat_id_telegram, message_validation)

  def execute_validation_reports(self):
    """
    Ejecuta la validación del reporte en el portal PDP.
    """
    logger.info("Iniciando validación del reporte en el portal PDP...")
    try:
      # Enviar mensaje informando inicio de la tarea
      self.telegram_bot.enviar_mensaje(
        self.info_portal.get("chat_id_telegram", ""),
        "▶️ Iniciando tarea de validación del portal PDP...")

      # Validar y enviar reporte de la pasarela de pagos de Monitoreo Por Estado
      self.validate_portal_pdp()

    except Exception as e:
      logger.exception(
        "Error durante la validación del reporte en el portal PDP.")
    finally:
      logger.info("Validación del reporte en el portal PDP finalizada.")
      # Enviar mensaje informando finalización de la tarea
    self.telegram_bot.enviar_mensaje(
      self.info_portal.get("chat_id_telegram", ""),
      "⏹️ Finalizando tarea de validación del portal PDP.")

  def run(self):
    """
    Ejecuta la tarea de validación del portal Bancoomeva.
    """

    screenshot_path = None
    try:
      # Abrir login del portal y esperar redireccionamiento al index
      self.init_login()

      while True:
        # Recargar cada 30 segundos la pagina para mantener la sesión activa
        self.page.reload()

        # Realizar la validacion del reporte
        minuto_actual = datetime.now().minute
        if minuto_actual == 1:
          self.execute_validation_reports()
        self.execute_validation_reports()
        # Esperar 30 segundos
        logger.info(
          f"Esperando 30 segundos antes de la siguiente recarga... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

        # Limpiar carpeta screenshots, de archivos que lleven más de 24 horas
        if self.screenshot_dir:
          try:
            delete_files_dir_time(self.screenshot_dir, max_age_minutes=60 * 24)
          except Exception as e:
            logger.warning(
              f"No se pudo limpiar la carpeta de capturas: {str(e)}")
            pass
        # Esperar 50 segundos antes de la siguiente recarga
        sleep(50)

    except Exception as e:
      logger.exception("Error durante la ejecución de la tarea de validación.")
      # Intentar tomar captura de pantalla en caso de error
      try:
        screenshot_path = self.take_screenshot(
          "error_portal_bancoomeva", error=True, full_page=False)
      except Exception:
        screenshot_path = None
      # Enviar mensaje de error por telegram
      error_message = f"❌ Error durante la ejecución de la tarea de validación del portal PDP: {str(e)}"
      self.telegram_bot.enviar_mensaje(
        self.info_portal.get("chat_id_telegram", ""), error_message)
      return {
          'status': 'ERROR',
          'screenshot_path': screenshot_path,
          'error': str(e)
      }
    finally:
      # Cerrar el navegador pase lo que pase
      try:
        # Cerrar navegador
        logger.info("Cerrando el navegador...")
        self.close_browser()
      except Exception as e:
        logger.warning(
          f"No se pudo cerrar el navegador correctamente: {str(e)}")
        pass
