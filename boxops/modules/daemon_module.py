import os
import signal
import subprocess
from pathlib import Path
import typer
from rich.console import Console

app = typer.Typer(help="Control del Vigilante en Segundo Plano (Telegram ChatOps)")
console = Console()

PID_FILE = Path("/opt/boxops/infra/daemon.pid")

@app.command("start")
def start_daemon():
    """Inicia el demonio de Telegram en segundo plano."""
    if PID_FILE.exists():
        console.print("[yellow]⚠️ El archivo PID existe. El daemon podría ya estar corriendo. Ejecuta 'boxops daemon stop' primero si hay problemas.[/yellow]")
        
    console.print(">> Levantando Telegram Poller (nohup)...")
    
    # Lanzamos el script aisladamente y redirigimos su salida a un archivo log
    import sys
    log_file = open("/opt/boxops/infra/daemon.log", "a")
    process = subprocess.Popen(
        [sys.executable, "-m", "boxops.utils.telegram_daemon"], 
        stdout=log_file, 
        stderr=subprocess.STDOUT,
        preexec_fn=os.setpgrp
    )
    
    # Guardamos el PID
    PID_FILE.write_text(str(process.pid))
    console.print(f"[bold green]✔ Daemon corriendo en segundo plano (PID: {process.pid}).[/bold green]")
    console.print("📱 Abre Telegram y envía /help para comprobar la conexión.")


@app.command("stop")
def stop_daemon():
    """Detiene el demonio actual activo de Telegram."""
    if not PID_FILE.exists():
        console.print("[dim]No hay registro de daemon activo (no existe daemon.pid).[/dim]")
        return
        
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        console.print(f"[bold green]✔ Proceso de Daemon (PID: {pid}) terminado satisfactoriamente.[/bold green]")
    except ProcessLookupError:
        console.print("[yellow]⚠️ El proceso no estaba corriendo ya, limpiando archivo fantasma.[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error al matar proceso: {e}[/red]")
        
    PID_FILE.unlink(missing_ok=True)

@app.command("status")
def status_daemon():
    """Chequea si el proceso del daemon está vivo en Linux."""
    if not PID_FILE.exists():
        console.print("[dim]El Telegram Daemon NO está corriendo (ausencia de daemon.pid).[/dim]")
        return
        
    pid = int(PID_FILE.read_text().strip())
    
    try:
        os.kill(pid, 0) # Checa liveness sin matarlo
        console.print(f"[bold green]✔ El Daemon está VIVO y respirando en el bloque PID {pid}.[/bold green]")
    except OSError:
        console.print(f"[bold red]❌ El Daemon está MUERTO pero dejó su PID {pid}. (Corrupción o Crash)[/bold red]")
        console.print("Ejecuta 'boxops daemon stop' para limpiar, revisa 'boxops daemon logs' y vuelve a iniciarlo.")

@app.command("logs")
def logs_daemon():
    """Mira los últimos 20 eventos del Daemon en texto plano."""
    log_path = Path("/opt/boxops/infra/daemon.log")
    if not log_path.exists():
        console.print("[dim]No hay archivo de logs generado por el momento.[/dim]")
        return
        
    console.print(f"[bold cyan]>> Últimas 20 líneas de {log_path}:[/bold cyan]")
    os.system(f"tail -n 20 {log_path}")

@app.command("config")
def config_daemon():
    """Reconfigura interactivamente las credenciales de Telegram para el Daemon."""
    from boxops.modules.infra_module import set_env_var
    
    console.print("[bold yellow]Reconfiguración Manual de ChatOps (Telegram)[/bold yellow]")
    
    token = typer.prompt("Introduce el nuevo Bot Token (entregado por BotFather)")
    chat_id = typer.prompt("Introduce el Telegram Chat ID (número negativo para grupos)")
    
    env_path = "/opt/boxops/infra/.env"
    set_env_var(env_path, "TELEGRAM_BOT_TOKEN", token)
    set_env_var(env_path, "TELEGRAM_CHAT_ID", chat_id)
    
    console.print(f"[bold green]✔ Credenciales de Telegram inyectadas en {env_path}[/bold green]")
    console.print("Recuerda ejecutar 'boxops daemon stop' y 'boxops daemon start' para que el vigilante adopte los nuevos tokens.")
