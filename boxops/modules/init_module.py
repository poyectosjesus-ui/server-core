import typer
from rich.console import Console

app = typer.Typer()
console = Console()

@app.command("config")
def config_server():
    """Generar la configuración base de seguridad y de sistema para este servidor."""
    console.print("[yellow]Escaneando configuración actual...[/yellow]")
    console.print("[green]✔ Configuración Firewall (UFW) aplicada idealmente. (MOCK)[/green]")
    console.print("[green]✔ Fail2Ban iniciado silenciosamente. (MOCK)[/green]")
