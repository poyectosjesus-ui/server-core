import time
import requests
import subprocess
from pathlib import Path

# Utilizamos las mismas utilidades previamente creadas
from boxops.utils.telegram import get_telegram_config, send_telegram_alert

APPS_DIR = Path("/opt/boxops/apps")

def escape_html(text: str) -> str:
    """Escapa caracteres HTML para envío seguro a Telegram."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def run_command(cmd_list, capture=True):
    try:
        res = subprocess.run(cmd_list, capture_output=capture, text=True, check=True)
        return True, res.stdout or ""
    except subprocess.CalledProcessError as e:
        return False, getattr(e, 'stderr', str(e))
    except Exception as e:
         return False, str(e)

def handle_help_command():
    msg = (
        "🤖 <b>BoxOps ChatOps Daemon v1.0</b>\n\n"
        "Comandos disponibles para controlar este servidor:\n\n"
        "📊 <b>/status</b> - Muestra CPU/RAM del clúster Infraestructural.\n"
        "📦 <b>/apps</b> - Lista las Cargas de Trabajo lanzadas.\n"
        "💾 <b>/backup</b> - Fuerza un Dump lógico de la BD AHORA mismo.\n"
        "❓ <b>/help</b> - Muestra este panel."
    )
    send_telegram_alert(msg)

def handle_status_command():
    send_telegram_alert("⏳ Recabando métricas de Telemetría (Docker Daemon)...")
    success, out = run_command(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}"])
    
    if not success:
        send_telegram_alert("❌ Error consultando el Docker Daemon.")
        return
        
    lines = out.strip().split("\n")
    report = "🔮 <b>Estado Global BoxOps</b>\n\n"
    
    for line in lines:
        if "boxops-" in line:
            parts = line.split("|")
            if len(parts) >= 3:
                name, cpu, mem = parts[0].replace("boxops-", ""), parts[1], parts[2]
                report += f"🔹 <b>{name}</b>\nCPU: {cpu} | RAM: {mem}\n\n"
                
    send_telegram_alert(report)

def handle_apps_command():
    if not APPS_DIR.exists():
        send_telegram_alert("ℹ️  Aún no tienes Cargas de Trabajo (Apps) instaladas.")
        return
        
    apps = [d.name for d in APPS_DIR.iterdir() if d.is_dir() and (d / "docker-compose.yml").exists()]
    if not apps:
         send_telegram_alert("ℹ️  No hay apps activas.")
         return
         
    report = "📦 <b>Workloads / Aplicaciones Vivas:</b>\n\n"
    for app in apps:
        success, out = run_command(["docker", "ps", "-f", f"name=boxops-app-{app}", "--format", "{{.Status}}"])
        status = out.strip() if success and out.strip() else "Apagada"
        report += f"🚀 <b>{app}</b> - <code>{status}</code>\n"
        
    send_telegram_alert(report)

def handle_backup_command():
    send_telegram_alert("⏳ <b>Forzando Snapshot Lógico:</b> Comunicándome con el contenedor de respaldos...")
    
    # Asegúrate de que el contenedor se llame boxops-db-backup y tenga config para ejecutar su entrypoint bkp.
    # Postgres-backup-local usa comúnmente /backup.sh
    success, out = run_command(["docker", "exec", "-t", "boxops-db-backup", "/backup.sh"])
    
    if success:
        send_telegram_alert("✅ <b>Backup Completado Exitosamente!</b> El archivo <code>.sql.gz</code> fue depositado localmente y en MinIO.")
    else:
        send_telegram_alert(f"❌ <b>Falla Taller de Backups:</b>\n<code>{escape_html(out)}</code>")


def start_polling():
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        print("❌ Faltan configuraciones (TOKEN o CHAT_ID) en /opt/boxops/infra/.env")
        return

    print(f"[*] Iniciando BoxOps Telegram Daemon escuchando a CHAT_ID: {chat_id}")
    
    offset = None
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    while True:
        try:
             params = {"timeout": 30}
             if offset:
                 params["offset"] = offset
                 
             response = requests.get(url, params=params, timeout=35)
             data = response.json()
             
             if not data.get("ok"):
                 time.sleep(5)
                 continue
                 
             for update in data.get("result", []):
                 offset = update["update_id"] + 1
                 
                 message = update.get("message")
                 if not message:
                     continue
                     
                 msg_chat_id = str(message.get("chat", {}).get("id"))
                 text = message.get("text", "").strip()
                 
                 # SEGURIDAD CRÍTICA: Impedir acceso de intrusos
                 if msg_chat_id != chat_id:
                     print(f"[!] Solicitud bloqueada del Chat Intrusi ID: {msg_chat_id}")
                     continue
                     
                 if text == "/help":
                     handle_help_command()
                 elif text == "/status":
                     handle_status_command()
                 elif text == "/apps":
                     handle_apps_command()
                 elif text == "/backup":
                     handle_backup_command()
                     
        except requests.exceptions.Timeout:
             continue # Timeout esperado en long polling
        except KeyboardInterrupt:
             print("\n[*] Deteniendo BoxOps Telegram Daemon.")
             break
        except Exception as e:
             print(f"[!] Error repentino en ciclo Daemon: {e}")
             time.sleep(5)

if __name__ == "__main__":
    start_polling()
