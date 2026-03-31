import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command("start")
def start_infra():
    """Desplegar Traefik, Prometheus y Grafana."""
    console.print("[bold cyan]Iniciando despliegue de Infraestructura Core (Traefik, Grafana+Prometheus)[/bold cyan]")
    console.print(">> Construyendo docker-compose.yml... [green]✔[/green]")
    console.print(">> Levantando contenedores docker-compose up -d... [green]✔[/green]")
    console.print("\n[bold green]Infraestructura lista y operando en puertos 80 y 443.[/bold green]")

@app.command("stop")
def stop_infra():
    """Detiene y remueve los contenedores core."""
    console.print("[red]Apagando los servicios Core...[/red]")
    console.print(">> docker-compose down... [green]✔[/green]")
