import requests
import json


class TelegramBot:
  """"Clase para interactuar con la API de Telegram y enviar mensajes y archivos.
  """

  def __init__(self, token):
    self.token = token
    self.base_url = f"https://api.telegram.org/bot{self.token}/"

  def enviar_mensaje(self, chat_id: str, texto: str):
    """Envía un mensaje de texto a un chat específico.

    Args:
        chat_id (str): ID del chat o canal donde se enviará el mensaje.
        texto (str): Contenido del mensaje a enviar.
    """
    url = self.base_url + "sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"  # Opcional: soporta Markdown o HTML
    }
    response = requests.post(url, json=payload)
    return response.json()

  def enviar_mensaje_con_archivos(self, chat_id: str, texto: str, archivos: list[str]):
    """Envía un mensaje de texto junto con múltiples archivos adjuntos a un chat específico.

    Args:
        chat_id (str): ID del chat o canal donde se enviará el mensaje.
        texto (str): Contenido del mensaje a enviar.
        archivos (list[str]): Lista de rutas de archivos a adjuntar.
    """
    if not archivos:
      return self.enviar_mensaje(chat_id, texto)

    url = self.base_url + "sendMediaGroup"
    media = []

    for i, archivo in enumerate(archivos):
      media_item = {
          "type": "document",
          "media": f"attach://{archivo}"
      }
      if i == len(archivos) - 1:
        media_item["caption"] = texto
        media_item["parse_mode"] = "Markdown"
      media.append(media_item)

    files = {}
    opened_files = []
    try:
      for archivo in archivos:
        f = open(archivo, 'rb')
        opened_files.append(f)
        files[archivo] = f

      data = {"chat_id": chat_id, "media": json.dumps(media)}
      response = requests.post(url, data=data, files=files)
      return response.json()
    finally:
      for f in opened_files:
        f.close()


if __name__ == "__main__":
  token = "8131060940:AAHlHCqvoTFBgKl0OnKtXskVe_GFMXKCqrs"
  chat_id = "1240514971"  # ID del chat o canal

  bot = TelegramBot(token)
  mensaje = "Hola, este es un mensaje de prueba desde el bot de Telegram."
  archivos = ["./base_class.py", "./constans.py"]  # Lista de archivos a enviar
  respuesta = bot.enviar_mensaje_con_archivos(chat_id, mensaje, archivos)
  print(respuesta)
