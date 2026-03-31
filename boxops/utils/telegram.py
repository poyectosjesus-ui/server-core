import os
import requests
from pathlib import Path

INFRA_ENV_FILE = Path("/opt/boxops/infra/.env")

def get_telegram_config():
    """Lee el archivo .env de BoxOps y retorna el TOKEN y el CHAT_ID, si existen."""
    if not INFRA_ENV_FILE.exists():
        return None, None
        
    token = None
    chat_id = None
    
    with open(INFRA_ENV_FILE, "r") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                token = line.split("=", 1)[1].strip()
            elif line.startswith("TELEGRAM_CHAT_ID="):
                chat_id = line.split("=", 1)[1].strip()
                
    return token, chat_id

def send_telegram_alert(message: str, parse_mode: str = "HTML") -> bool:
    """Envía un mensaje asíncrono pasivo a Telegram. Falla silenciosamente para no retrasar la CLI."""
    token, chat_id = get_telegram_config()
    
    # Si el usuario no configuró el Bot en el Wizard, salir elegantemente
    if not token or not chat_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        # Timeout corto (3 segs) para que BoxOps no se quede trabado si la API de Telegram se cuelga
        r = requests.post(url, json=payload, timeout=3)
        return r.status_code == 200
    except Exception:
        # Fallar en silencio si no hay internet o error de requests
        return False
