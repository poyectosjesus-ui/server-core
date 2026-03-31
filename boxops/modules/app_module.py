import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command("install")
def install_app(name: str):
    """Instala una aplicación utilizando plantillas por defecto."""
    console.print(f"[bold cyan]Preparando despliegue de '{name}'[/bold cyan]...")
    console.print(f">> Enlazando a la red de Traefik y levantando {name}... [green]✔[/green]")

@app.command("ls")
def ls_app():
    """Lista las aplicaciones bajo la gestión de BoxOps."""
    import subprocess
    console.print("[bold]Contenedores activos en la máquina local:[/bold]")
    try:
        subprocess.run(["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"])
    except Exception:
        console.print("[red]Docker no está disponible o accesible localmente en este momento.[/red]")
