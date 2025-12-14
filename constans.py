SELECTOR_REPORT_CONSULT="li[id$='pm_consulta'] a"
ROWS_TABLE_REPORT_CONSULT=[
  "Comercio",
  "Fecha",
  "# Aprobadas",
  "# Rechazada",
  "# Fallidas",
  "# Pendiente EF",
  "# No Finales EF",
  "# No Finales",
  "# No Reportaadas",
  "Última Reportada",
]

MAX_VALUES_PER_PAGE = 22

SELECTORS_REPORT_CONSULT_OPTIONS={
  "Monitoreo Por Estado":{
    "selector": "li[id$='pm_consulta_admon_01'] a",
    "url": "https://ftpayment.co/FTAdmon_Payment-web/pages/consulta/consultaConsolidada01.xhtml",
    "url_fragment": "consultaConsolidada01.xhtml"
  }
}

SELECTOR_WAIT_LOADING="div img[src*='preloader.gif.xhtml']"

IGNORE_COMERCIOS_VALIDATIONS={
  "failures_vs_approvals": [
    "CAFAM"
  ]
}