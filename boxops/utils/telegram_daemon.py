import time
import requests
import subprocess
import threading
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
        "🤖 <b>BoxOps ChatOps Daemon v1.0 (DevSecOps Shield)</b>\n\n"
        "Comandos disponibles para controlar este servidor:\n\n"
        "📊 <b>/status</b> - Muestra CPU/RAM del clúster Infraestructural.\n"
        "📦 <b>/apps</b> - Lista las Cargas de Trabajo lanzadas.\n"
        "💾 <b>/backup</b> - Fuerza un Dump lógico de la BD AHORA mismo.\n"
        "🛑 <b>/kill &lt;app&gt;</b> - Frena abruptamente un contenedor infectado (Ej. /kill miapi).\n"
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

def handle_kill_command(text: str):
    parts = text.split(" ")
    if len(parts) < 2:
        send_telegram_alert("⚠️ Uso correcto: <code>/kill nombre-de-la-app</code>")
        return
        
    target_app = parts[1].strip()
    send_telegram_alert(f"🛑 <b>Kill Switch:</b> Ejecutando Kernel SIGTERM sobre <code>{target_app}</code>...")
    
    # Intenta parar el contenedor asociado a esa app específica
    success, out = run_command(["docker", "stop", f"boxops-app-{target_app}"])
    if success:
        send_telegram_alert(f"✅ <b>Éxito Operativo:</b> La amenaza '{target_app}' ha sido Neutralizada (Container Stopped).")
    else:
        send_telegram_alert(f"❌ <b>Error al neutralizar:</b>\n<code>{escape_html(out)}</code>")


# Tracker para monitoreo activo
def active_monitor_loop(token, chat_id):
    """Monitorea el CPU cada 60s. Si un contenedor supera el 85% por 3 min (3 strikes), emite Push Alert."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    strikes = {}
    
    while True:
        try:
            success, out = run_command(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}", "--no-trunc"])
            if not success:
                time.sleep(60)
                continue
                
            current_containers = []
            for line in out.strip().split("\n"):
                if not line or "|" not in line:
                    continue
                    
                parts = line.split("|")
                name = parts[0].strip()
                cpu_str = parts[1].replace("%", "").strip()
                
                try:
                    cpu_usage = float(cpu_str)
                except ValueError:
                    cpu_usage = 0.0
                    
                current_containers.append(name)
                
                # Regla: > 85% CPU es anomalía
                if cpu_usage > 85.0:
                    strikes[name] = strikes.get(name, 0) + 1
                    
                    if strikes[name] == 3:
                        msg = (
                            f"🚨 <b>¡ALERTA ROJA (DevSecOps)!</b> 🚨\n\n"
                            f"El contenedor <code>{name}</code> lleva 3 minutos operando al <b>{cpu_usage}% CPU</b>.\n\n"
                            f"Posible Anomalía o Software de Criptominería infiltrado.\n"
                            f"Responde <code>/kill {name.replace('boxops-app-', '')}</code> para forzar apagado remoto desde este chat."
                        )
                        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=5)
                else:
                    # Se calmó la CPU, limpiamos el strike
                    if name in strikes:
                        del strikes[name]
            
            # Limpiar contenedores que ya no existen
            for k in list(strikes.keys()):
                if k not in current_containers:
                    del strikes[k]
                    
        except Exception as e:
            print(f"[!] Error en Thread Monitor Activo: {e}")
            
        # Esperar 60 segundos antes del siguiente escaneo
        time.sleep(60)

def start_polling():
    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        print("❌ Faltan configuraciones (TOKEN o CHAT_ID) en /opt/boxops/infra/.env")
        return

    print(f"[*] Iniciando BoxOps Telegram Daemon escuchando a CHAT_ID: {chat_id}")
    
    # Lanzar el Hilo (Thread) Activo del DevSecOps Anti-Miner
    monitor_thread = threading.Thread(target=active_monitor_loop, args=(token, chat_id), daemon=True)
    monitor_thread.start()
    print("[*] Thread de Telemetría Activa (CPU Tracker) inicializado.")
    
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
                 elif text.startswith("/kill "):
                     handle_kill_command(text)
                     
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
