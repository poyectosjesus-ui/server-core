import typer
from rich.console import Console
from .modules import init_module, infra_module, app_module, db_module, remote_module

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

from .modules.app_module import push_app
app.command("push", help="[Remoto] Sube el proyecto actual al servidor configurado")(push_app)

@app.command()
def version():
    """Muestra la versión actual del CLI."""
    from . import __version__
    console.print(f"[bold bright_blue]BoxOps CLI[/bold bright_blue] version {__version__}")
    console.print("Construido para administración MVP ✨")

if __name__ == "__main__":
    app()
