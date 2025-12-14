import requests
import json
import base64
import time
from urllib.parse import quote


def xor_encrypt(text, key):
    """Aplica XOR entre el texto y la clave de forma circular (simétrico)"""
    result = []
    key_length = len(key)
    
    for i in range(len(text)):
        xor_value = ord(text[i]) ^ ord(key[i % key_length])
        result.append(chr(xor_value))
    
    return ''.join(result)


def encrypt_param_cache(plain_data, key):
    """
    Cifra datos usando el algoritmo XOR con doble Base64
    Retorna: (encrypted_data, timestamp)
    """
    timestamp = str(int(time.time() * 1000))
    
    # 1. Codificar URI component
    uri_encoded = quote(plain_data, safe='')
    
    # 2. Codificar Base64 interno
    base64_encoded = base64.b64encode(uri_encoded.encode('utf-8')).decode('utf-8')
    
    # 3. Aplicar XOR para cifrar
    xor_encrypted = xor_encrypt(base64_encoded, key)
    
    # 4. Codificar Base64 externo
    final_encrypted = base64.b64encode(xor_encrypted.encode('latin-1')).decode('utf-8')
    
    return final_encrypted, timestamp


def get_params_encrypt(url, jwt_token, key_encryption, verify_ssl=True):
    """
    Obtiene los parámetros del portal desde la API, los procesa y los encripta.
    
    :param url: URL del API de paramétros del portal
    :param jwt_token: Token JWT para la autenticación
    :param id_commerce: ID del comercio para el cual se obtendrán los parámetros
    :param key_encryption: Clave de encriptación (por defecto: "coomeva_portal_multiservices_2024")
    :param verify_ssl: Booleano para verificar SSL en la petición (default: True)
    :return: Tupla con (param_cache_encrypted, timestamp, data_original) o (None, None, None) si hay error
    """
    try:
        # Configurar headers con autenticación Bearer
        headers = {
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"🌐 Haciendo petición a: {url}")
        print(f"🔑 Token: {jwt_token[:20]}..." if len(jwt_token) > 20 else f"🔑 Token: {jwt_token}")
        
        # Hacer la petición GET
        response = requests.get(url, headers=headers, timeout=30, verify=verify_ssl)
        
        # Verificar si la respuesta fue exitosa
        response.raise_for_status()
        
        # Obtener el JSON de la respuesta
        response_json = response.json()
        
        print(f"✅ Respuesta recibida: {response.status_code}")
        
        # Extraer los datos (normalmente vienen en response.data)
        if 'data' in response_json and response_json['data']:
            data = response_json['data']
        else:
            print("⚠️ No se encontró 'data' en la respuesta, usando respuesta completa")
            data = response_json
        
        # Verificar que haya datos
        if not data or (isinstance(data, dict) and len(data) == 0):
            print("⚠️ No hay datos para presentar")
            return None, None, None
        
        # Convertir a JSON string SIN espacios ni saltos de línea (compacto)
        json_string = json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        
        print(f"📝 JSON generado: {len(json_string)} caracteres")
        print(f"   Primeros 150 chars: {json_string[:150]}...")
        
        # Encriptar el JSON
        print(f"\n🔒 Encriptando con clave: {key_encryption}")
        encrypted, timestamp = encrypt_param_cache(json_string, key_encryption)
        
        print(f"✅ Encriptación exitosa")
        print(f"   param_cache: {len(encrypted)} caracteres")
        print(f"   timestamp: {timestamp}")
        
        return encrypted, timestamp, data
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error HTTP: {e}")
        print(f"   Status Code: {response.status_code}")
        print(f"   Respuesta: {response.text[:500]}")
        return None, None, None
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Error de conexión: {e}")
        return None, None, None
        
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout: {e}")
        return None, None, None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error en la petición: {e}")
        return None, None, None
        
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON: {e}")
        print(f"   Respuesta raw: {response.text[:500]}")
        return None, None, None
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None
    