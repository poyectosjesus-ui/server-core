import os
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Gestión del entorno Cliente-Servidor de BoxOps (Deploy Remoto)")
console = Console()

CONFIG_DIR = Path.home() / ".boxops"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

@app.command("add")
def remote_add(ip: str = typer.Argument(..., help="IP del servidor remoto")):
    """Registra la conexión SSH hacia el servidor BoxOps en la infraestructura."""
    user = typer.prompt("Usuario SSH (ej. core, root)", default="core")
    port = typer.prompt("Puerto SSH", default="22")
    
    config = load_config()
    config["remote"] = {
        "ip": ip,
        "user": user,
        "port": port
    }
    save_config(config)
    
    console.print(f"[bold green]✔ Servidor Remoto apuntado a {user}@{ip}:{port}[/bold green]")
    console.print("[dim]Ahora puedes ir a la carpeta de tus repositorios locales y hacer `boxops push`.[/dim]")

@app.command("status")
def remote_status():
    """Muestra el servidor remoto activo en la máquina local."""
    config = load_config()
    remote = config.get("remote")
    if not remote:
        console.print("[yellow]No hay un servidor remoto configurado. Usa `boxops remote add`.[/yellow]")
        return
        
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Servidor Activo")
    table.add_column("SSH String")
    
    ssh_str = f"ssh -p {remote['port']} {remote['user']}@{remote['ip']}"
    table.add_row(remote['ip'], ssh_str)
    console.print(table)
