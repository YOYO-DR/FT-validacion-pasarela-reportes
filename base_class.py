import logging
import os
import re
from datetime import datetime
from time import sleep
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
      if not  context:
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

  def wait_and_validate_visible(self, selector: str, timeout: int = None)-> bool:
    """
    Espera a que un elemento exista y sea visible en la página.
    :param selector: Selector CSS del elemento a esperar.
    :param timeout: Tiempo máximo en milisegundos para esperar.
    :return: El elemento localizado si es visible.
    """
    try:
      logger.info(f"Esperando a que el elemento sea visible: {selector}")
      self.page.wait_for_selector(selector, state="attached", timeout=timeout or self.max_wait)
      self.page.wait_for_selector(selector, state="visible", timeout=timeout or self.max_wait)
      return True
    except PlaywrightTimeoutError:
      logger.warning(f"Tiempo de espera agotado para que el elemento sea visible: {selector}")
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

  def init_login(self):
    """
    Inicializa el proceso de login en el portal administrativo de la pasarela. Espera el redireccionamiento al index.
    """
    logger.info("Iniciando login en el portal PDP...")
    url_login = self.info_portal.get("url_portal_pdp")
    if not url_login:
      raise ValueError("La URL del portal PDP no está definida en info_portal.")
    # Lanzar el navegador y abrir la página de login
    self.launch_browser()
    self.launch_page(url_login)
    
    # Esperar a que se redireccione al index después del login, esperar almenos 60 segundos
    self.page.wait_for_url("https://ftpayment.co/FTAdmon_Payment-web/pages/index.xhtml", timeout=60*1000)

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

    # Hacer clic en el menú de consulta de reportes
    self.click_first_visible_match(SELECTOR_REPORT_CONSULT)

    # Abrir opcion de reporte específica
    report_option = SELECTORS_REPORT_CONSULT_OPTIONS.get(report_name)
    if not report_option:
      raise ValueError(f"El reporte '{report_name}' no está definido en SELECTORS_REPORT_CONSULT_OPTIONS.")
    
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
      screenshot_path = table_locator.screenshot(path= os.path.join(self.screenshot_dir, f"table_page_{page + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"))
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
    logger.info("Validando que no haya más transacciones Fallidas que Aprobadas por comercio...")
    comersios_with_issues = []

    for row in data_table:
      comercio = row["Comercio"]
      # Validar si se debe ignorar este comercio
      if comercio in IGNORE_COMERCIOS_VALIDATIONS.get("failures_vs_approvals", []):
        logger.info(f"Ignorando validación para el comercio: {comercio}")
        continue
      aprobadas = int(row["# Aprobadas"].replace(",", "") or "0")
      fallidas = int(row["# Fallidas"].replace(",", "") or "0")

      if fallidas > aprobadas:
        comersios_with_issues.append(comercio)
    
    logger.info("Validación exitosa: No hay más transacciones Fallidas que Aprobadas por comercio.")

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

    # 1. Validar que no hayan más transacciones Fallidas que Aprobadas por comercio
    self.validate_failures_vs_approvals(data_table)

  def validate_portal_pdp(self):
    """
    Realiza la validación del portal PDP, reporte monitoreo por estado.
    """

    # Abrir vista de consulta "Monitoreo Por Estado"
    self.open_report_view("Monitoreo Por Estado")

    # Ejecutar consulta del reporte y extraer datos de la tabla
    data_table, screenshots_table = self.exe_consult_and_ext_data()

    # Validar información extraída
    self.validate_report_data(data_table)
    
    




    # Seleccionar factura, marcar casillas
    self.select_invoice()
    # Procesar pago
    time_loading_checkout = self.process_payment()
    # Cancelar el pago para no completar la transacción y volver al portal
    self.return_to_portal()
    logger.info(f"Tiempo de carga del checkout: {time_loading_checkout:.2f} segundos.")
    # Generar captura de pantalla final
    screenshot_path=self.take_screenshot("final_portal_bancoomeva", full_page=False)
    # Enviar correo con resultados
    # _send_success_notification()
    return {
              'status': 'SUCCESS',
              'screenshot_path': screenshot_path,
              'task_id': self.task_id
          }

  def execute_validation_reports(self):
    """
    Ejecuta la validación del reporte en el portal PDP.
    """

    # Validar y enviar reporte de la pasarela de pagos de Monitoreo Por Estado
    self.validate_portal_pdp()
    

  def run(self):
    """
    Ejecuta la tarea de validación del portal Bancoomeva.
    """
    screenshot_path = None
    try:
      # Abrir login del portal y esperar redireccionamiento al index
      self.init_login()

      while True:
        # Recargar cada 60 segundos la pagina para mantener la sesión activa
        self.page.reload()

        # Realizar la validacion del reporte
        if self.info_portal.get("execute_report_validation", True):
          self.execute_validation_reports()
        # Esperar 60 segundos
        logger.info(f"Esperando 60 segundos antes de la siguiente recarga... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        sleep(60)

      
    
    except Exception as e:
      logger.exception("Error durante la ejecución de la tarea de validación.")
      # Intentar tomar captura de pantalla en caso de error
      try:
        screenshot_path=self.take_screenshot("error_portal_bancoomeva", error=True, full_page=False)
      except Exception:
        screenshot_path = None
      return {
                'status': 'ERROR',
                'screenshot_path': screenshot_path,
                'error': str(e)
            }
    finally:
      # Cerrar el navegador pase lo que pase
      try:
        logger.info("Cerrando el navegador...")
        self.close_browser()
      except Exception as e:
        logger.warning(f"No se pudo cerrar el navegador correctamente: {str(e)}")
        pass
  