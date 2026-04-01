import typer
from rich.console import Console
from .modules import init_module, infra_module, app_module, db_module, remote_module, daemon_module

app = typer.Typer(
    name="boxops",
    help="🚀 BoxOps v1.0.0 - Server Management & Provisioning CLI",
    add_completion=False,
)

console = Console()

app.add_typer(init_module.app, name="init", help="Configura la máquina base (UFW, utilidades).")
app.add_typer(infra_module.app, name="infra", help="Gestiona Traefik y Monitoreo (Grafana/Prometheus).")
app.add_typer(db_module.app, name="db", help="Gestión de Bases de Datos (Dedicadas / Lógicas aisladas).")
app.add_typer(app_module.app, name="app", help="Gestiona instalación y bajada de contenedores genéricos.")
app.add_typer(remote_module.app, name="remote", help="Gestiona conexiones y despliegues remotos.")
app.add_typer(daemon_module.app, name="daemon", help="Inicia/Detiene el vigilante de Telegram ChatOps.")

from .modules.app_module import push_app
app.command("push", help="[Remoto] Sube el proyecto actual al servidor configurado")(push_app)

@app.command("status")
def global_status():
    """Muestra el Dashboard de Salud Global (Docker, Traefik, Backups)."""
    import subprocess
    from rich.table import Table
    from rich.panel import Panel
    from pathlib import Path
    import os
    import time

    console.print(Panel("[bold cyan]🔮 BoxOps Global Health Dashboard[/bold cyan]", expand=False))

    try:
        res = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}"], capture_output=True, text=True, check=True)
    except Exception:
        console.print("[red]❌ Error conectando al Docker Daemon.[/red]")
        return
        
    lines = res.stdout.strip().split("\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Container")
    table.add_column("CPU %")
    table.add_column("RAM Usage")
    table.add_column("RAM %")
    
    boxops_ok = 0
    for line in lines:
        if not line: continue
        parts = line.split("|")
        if len(parts) >= 4:
            name, cpu, mem_use, mem_perc = parts[0], parts[1], parts[2], parts[3]
            if name.startswith("boxops-"):
                boxops_ok += 1
                try:
                    c_val = float(cpu.replace('%','').strip())
                    cpu_color = "red" if c_val > 80 else ("yellow" if c_val > 50 else "green")
                except ValueError: cpu_color = "white"
                
                try:
                    m_val = float(mem_perc.replace('%','').strip())
                    ram_color = "red" if m_val > 80 else ("yellow" if m_val > 50 else "green")
                except ValueError: ram_color = "white"
                
                table.add_row(name.replace("boxops-", ""), f"[{cpu_color}]{cpu}[/{cpu_color}]", mem_use, f"[{ram_color}]{mem_perc}[/{ram_color}]")
    
    if boxops_ok == 0:
         console.print("[dim]No se encontraron servicios de BoxOps activos.[/dim]")
    else:
         console.print(table)
         
    # Backup Checks
    console.print("\n[bold yellow]🛡️  Respaldos Base de Datos:[/bold yellow]")
    bkp_dir = Path("/opt/boxops/infra/backups/backup-files/globaldb")
    if bkp_dir.exists():
        files = sorted(bkp_dir.glob("*.sql.gz"), key=os.path.getmtime, reverse=True)
        if files:
            last = files[0]
            size_mb = last.stat().st_size / (1024 * 1024)
            age_hours = (time.time() - last.stat().st_mtime) / 3600
            
            color = "green" if age_hours < 26 else "red"
            console.print(f"[{color}]Último Dump: {last.name} (Hace {age_hours:.1f} hrs) | {size_mb:.1f} MB[/{color}]")
        else:
            console.print("[red]⚠️ No hay archivos de respaldo SQL encontrados en la carpeta globaldb.[/red]")
    else:
        console.print("[dim]Servicio automático no ha emitido el folder globaldb, o contenedor apagado.[/dim]")

@app.command()
def version():
    """Muestra la versión actual del CLI."""
    from . import __version__
    console.print(f"[bold bright_blue]BoxOps CLI[/bold bright_blue] version {__version__}")
    console.print("Construido para administración MVP ✨")


@app.command("update")
def update_cli():
    """Descarga la última versión de BoxOps desde GitHub y recompila el motor."""
    import subprocess
    from pathlib import Path
    
    install_dir = Path("/opt/boxops")
    if not install_dir.exists() or not (install_dir / ".git").exists():
        console.print("[red]❌ La CLI no fue instalada vía clonación Git en /opt/boxops. No se puede auto-actualizar.[/red]")
        return
        
    console.print("[bold cyan]>> Sincronizando repositorios desde GitHub (main)...[/bold cyan]")
    try:
        subprocess.run(["git", "pull", "origin", "main"], cwd=install_dir, check=True)
        console.print("[bold cyan]>> Recompilando dependencias de Python (pip)...[/bold cyan]")
        subprocess.run(["/opt/boxops/venv/bin/pip", "install", "-e", "."], cwd=install_dir, check=True)
        console.print("[bold green]✔ BoxOps ha sido sincronizado a la última versión arquitectónica Exitosamente.[/bold green]")
    except Exception as e:
        console.print(f"[bold red]❌ Error de Sincronización GitHub:[/bold red] {e}")


@app.command("uninstall")
def uninstall_cli():
    """Elimina agresivamente el código fuente y ejecutables de BoxOps de esta máquina."""
    import subprocess
    import typer
    
    console.print("[bold red]⚠️  ¡ADVERTENCIA DE AUTODESTRUCCIÓN! ⚠️[/bold red]")
    console.print("Esto borrará todo el código base de `/opt/boxops/` y desligará el binario `boxops`.")
    console.print("Tus contenedores Docker y datos creados seguirán operando, pero perderás acceso a la CLI para gestionarlos.\n")
    
    if typer.confirm("¿Estás absolutamente seguro de erradicar a BoxOps de este servidor?", default=False):
        console.print("[dim]>> Purgando Binarios SysAdmin...[/dim]")
        subprocess.run(["sudo", "rm", "-f", "/usr/local/bin/boxops"])
        console.print("[dim]>> Quemando repositorios fuente...[/dim]")
        subprocess.run(["sudo", "rm", "-rf", "/opt/boxops/"])
        console.print("[bold green]✔ Desinstalación Completada. Ha sido un honor servirte.[/bold green]")


from .modules.daemon_module import config_daemon
app.command("botconfig", help="Acceso directo rápido a re-configurar Tokens de Telegram")(config_daemon)


if __name__ == "__main__":
    app()
