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
    
    # Lanzamos el script aisladamente de este proceso padre
    # Usamos sys.executable para garantizar que usa el mismo venv/python con el que corrió typer
    import sys
    process = subprocess.Popen(
        [sys.executable, "-m", "boxops.utils.telegram_daemon"], 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL,
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
