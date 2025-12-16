import requests
import json
import logging

# Inicialización del logger
logger = logging.getLogger(__name__)

class TelegramBot:
  """"Clase para interactuar con la API de Telegram y enviar mensajes y archivos.
  """

  def __init__(self, token):
    self.token = token
    self.base_url = f"https://api.telegram.org/bot{self.token}/"

  def enviar_mensaje(self, chat_ids: list | str, texto: str):
    """Envía un mensaje de texto a uno o varios chats.

    Args:
        chat_ids (list | str): ID(s) del chat o canal.
        texto (str): Contenido del mensaje a enviar.
    """
    if isinstance(chat_ids, str):
        chat_ids = [chat_ids]

    url = self.base_url + "sendMessage"
    results = []
    
    for chat_id in chat_ids:
        logger.info(f"Enviando mensaje a chat_id: {chat_id}")
        payload = {
            "chat_id": chat_id,
            "text": texto,
            "parse_mode": "Markdown"  # Opcional: soporta Markdown o HTML
        }
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            results.append(response.json())
            logger.info(f"Mensaje enviado exitosamente a {chat_id}")
        except Exception as e:
            logger.error(f"Error enviando mensaje a {chat_id}: {e}")

    return results

  def enviar_mensaje_con_archivos(self, chat_ids: list | str, texto: str, archivos: list[str]):
    """Envía un mensaje de texto junto con múltiples archivos adjuntos a uno o varios chats.

    Args:
        chat_ids (list | str): ID(s) del chat o canal.
        texto (str): Contenido del mensaje a enviar.
        archivos (list[str]): Lista de rutas de archivos a adjuntar.
    """
    if isinstance(chat_ids, str):
        chat_ids = [chat_ids]

    try:
      if not archivos:
        return self.enviar_mensaje(chat_ids, texto)

      url = self.base_url + "sendMediaGroup"
      media = []
      files = {}
      opened_files = []
      try:
        for i, archivo in enumerate(archivos):
          # Usar un nombre de archivo seguro para el adjunto
          attachment_key = f"file_{i}"
          
          media_item = {
              "type": "document",
              "media": f"attach://{attachment_key}"
          }
          if i == len(archivos) - 1:
            media_item["caption"] = texto
            media_item["parse_mode"] = "Markdown"
          media.append(media_item)

          f = open(archivo, 'rb')
          opened_files.append(f)
          files[attachment_key] = f

        results = []
        for chat_id in chat_ids:
            logger.info(f"Enviando mensaje con archivos a chat_id: {chat_id}")
            # Asegurar que los archivos se lean desde el inicio para cada request
            for f in opened_files:
                f.seek(0)

            data = {"chat_id": chat_id, "media": json.dumps(media)}
            try:
                response = requests.post(url, data=data, files=files)
                response.raise_for_status()
                results.append(True)
            except Exception as e:
                logger.exception(f"Error al enviar mensaje con archivos a {chat_id}: {str(e)}")
                results.append(False)
        
        return results
      finally:
        for f in opened_files:
          f.close()
    except Exception as e:
      logger.exception(f"Error general al enviar mensaje con archivos: {str(e)}")
      return []


if __name__ == "__main__":
  token = "8131060940:AAHlHCqvoTFBgKl0OnKtXskVe_GFMXKCqrs"
  chat_id = "1240514971"  # ID del chat o canal

  bot = TelegramBot(token)
  mensaje = "Hola, este es un mensaje de prueba desde el bot de Telegram."
  archivos = ["./base_class.py", "./constans.py"]  # Lista de archivos a enviar
  respuesta = bot.enviar_mensaje_con_archivos(chat_id, mensaje, archivos)
  print(respuesta)
