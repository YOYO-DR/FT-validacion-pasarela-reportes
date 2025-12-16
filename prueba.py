from base_class import ValidationPortalBancoomeva
import os
import logging

# Configurar logging para ver la salida en la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    # Directorio para capturas de pantalla
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    if not os.path.exists(screenshot_dir):
        os.makedirs(screenshot_dir)

    # Configuración del portal
    info_portal = {
        # Puedes agregar aquí configuraciones adicionales si son necesarias
    }

    print("Iniciando prueba de ValidationPortalBancoomeva...")
    task = ValidationPortalBancoomeva(headless=False, screenshot_dir=screenshot_dir, info_portal=info_portal)
    try:
        task.run()
    except KeyboardInterrupt:
        print("Prueba detenida por el usuario.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
