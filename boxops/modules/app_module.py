import subprocess
from pathlib import Path
import typer
import questionary
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Gestión de Aplicaciones (Workloads) con orquestación automática en Traefik")
console = Console()

APPS_DIR = Path("/opt/boxops/apps")

def run_command(cmd_list: list, cwd: Path = None, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run(cmd_list, check=True, cwd=cwd, capture_output=True, text=True)
            return True, result.stdout
        else:
            subprocess.run(cmd_list, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if capture_output else ""

@app.command("deploy")
def deploy_app():
    """Despliega una nueva aplicación genérica detrás de Traefik."""
    console.print("[bold bright_blue]🚀 Despliegue Dinámico de Aplicación[/bold bright_blue]")
    
    app_name = typer.prompt("Nombre único para la app (sin espacios)", type=str).lower().strip()
    app_image = typer.prompt("Imagen de Docker (ej. nginx:alpine, mi-registry/node-api:v1)", type=str)
    app_port = typer.prompt("Puerto interno EXPOSE sobre el que escucha el contenedor", type=int, default=80)
    app_domain = typer.prompt("Dominio público de enrutamiento (ej. api.midominio.com)", type=str)
    
    app_dir = APPS_DIR / app_name
    
    if app_dir.exists():
        console.print(f"[yellow]⚠️ La aplicación '{app_name}' ya existe. Esto la actualizará o sobreescribirá.[/yellow]")
        if not typer.confirm("¿Continuar?"):
            return
            
    app_dir.mkdir(parents=True, exist_ok=True)
    
    compose_content = f"""version: "3.8"
services:
  {app_name}:
    image: {app_image}
    container_name: boxops-app-{app_name}
    restart: unless-stopped
    networks:
      - boxops-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{app_name}.rule=Host(`{app_domain}`)"
      - "traefik.http.routers.{app_name}.entrypoints=websecure"
      - "traefik.http.routers.{app_name}.tls=true"
      - "traefik.http.routers.{app_name}.tls.certresolver=myresolver"
      - "traefik.http.services.{app_name}.loadbalancer.server.port={app_port}"

networks:
  boxops-network:
    external: true
"""
    (app_dir / "docker-compose.yml").write_text(compose_content)
    
    console.print(f"\\n>> Conectando '{app_name}' a la red de descubrimiento Traefik...")
    success, _ = run_command(["docker", "compose", "up", "-d"], cwd=app_dir)
    
    if success:
        console.print(f"[bold green]✔ Aplicación '{app_name}' en línea.[/bold green]")
        console.print(f"🌍 Disponible (con SSL automático) en: [bold underline]https://{app_domain}[/bold underline]")
        from boxops.utils.telegram import send_telegram_alert
        send_telegram_alert(f"🚢 <b>Deploy Local</b>: Workload <code>{app_name}</code> desplegado exitosamente en <b>{app_domain}</b>.")
    else:
        console.print(f"[bold red]❌ Hubo un error levantando el contenedor '{app_name}'.[/bold red]")


@app.command("list")
def list_apps():
    """Lista las aplicaciones registradas y corriendo bajo BoxOps."""
    console.print("[bold cyan]Cargas de Trabajo (Apps) Gestionadas:[/bold cyan]")
    
    if not APPS_DIR.exists():
        console.print("[dim]No hay directorio de aplicaciones creado aún.[/dim]")
        return
        
    apps = [d for d in APPS_DIR.iterdir() if d.is_dir() and (d / "docker-compose.yml").exists()]
    
    if not apps:
        console.print("[dim]No hay aplicaciones desplegadas.[/dim]")
        return
        
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("App Name")
    table.add_column("Container Status")
    
    for app in apps:
        app_name = app.name
        # Fetching status
        success, out = run_command(["docker", "ps", "-f", f"name=boxops-app-{app_name}", "--format", "{{.Status}}"], capture_output=True)
        status = out.strip() if success and out.strip() else "[red]Apagada / No encontrada[/red]"
        table.add_row(app_name, status)
        
    console.print(table)


@app.command("remove")
def remove_app():
    """Da de baja una aplicación seleccionada interactivamente."""
    if not APPS_DIR.exists():
        console.print("[dim]No hay aplicaciones para eliminar.[/dim]")
        return
        
    apps = [d.name for d in APPS_DIR.iterdir() if d.is_dir() and (d / "docker-compose.yml").exists()]
    if not apps:
        console.print("[dim]No hay aplicaciones registradas de BoxOps.[/dim]")
        return
        
    app_to_remove = questionary.select("Elige la aplicación que deseas DESTRUIR:", choices=apps).ask()
    
    if not app_to_remove:
        return
        
    if typer.confirm(f"⚠️ ¿Estás COMPLETAMENTE SEGURO de eliminar '{app_to_remove}' y sus datos anclados?", default=False):
        app_dir = APPS_DIR / app_to_remove
        console.print(f">> Bajando contenedor de '{app_to_remove}'...")
        run_command(["docker", "compose", "down", "-v"], cwd=app_dir)
        
        # Eliminar carpeta
        import shutil
        shutil.rmtree(app_dir)
        console.print(f"[bold green]✔ Aplicación '{app_to_remove}' destruida y removida del Proxy.[/bold green]")


def push_app():
    """Rsyncs local config to remote and triggers remote deployment."""
    import sys
    
    # Esto asume que el comando corre desde la máquina del DevOps.
    from boxops.modules.remote_module import load_config
    
    config = load_config().get("remote")
    if not config:
        console.print("[red]❌ No hay servidor remoto configurado. Ejecuta 'boxops remote add <ip>'.[/red]")
        sys.exit(1)
        
    current_dir = Path.cwd()
    app_name = typer.prompt("Nombre único para la app (sin espacios)", default=current_dir.name).lower().strip()
    
    ip = config["ip"]
    user = config["user"]
    port = config["port"]
    
    console.print(f"[bold cyan]>> Sincronizando código fuente '{app_name}' a {ip}...[/bold cyan]")
    
    rsync_cmd = [
        "rsync", "-avz", "--delete",
        "--exclude", ".git", "--exclude", "venv", "--exclude", "node_modules", "--exclude", "__pycache__",
        "-e", f"ssh -p {port}",
        f"{current_dir}/",
        f"{user}@{ip}:/tmp/boxops-upload-{app_name}/"
    ]
    
    success, out = run_command(rsync_cmd, capture_output=True)
    if not success:
        console.print(f"[red]Error sincronizando:[/red]\\n{out}")
        return
        
    console.print(f"\\n[bold cyan]>> Invocando BoxOps Remoto de forma interactiva...[/bold cyan]")
    
    ssh_cmd = [
        "ssh", "-t", "-p", str(port), f"{user}@{ip}",
        f"sudo mkdir -p /opt/boxops/apps && sudo rsync -a /tmp/boxops-upload-{app_name}/ /opt/boxops/apps/{app_name}/ && sudo rm -rf /tmp/boxops-upload-{app_name} && sudo boxops app remote-setup {app_name}"
    ]
    
    try:
        subprocess.run(ssh_cmd) # Bind to terminal TTY so prompts work seamlessly via SSH
    except FileNotFoundError:
        console.print("[red]Error: comando ssh no disponible en local.[/red]")


@app.command("remote-setup", hidden=True)
def remote_setup(app_name: str = typer.Argument(...)):
    """(Remoto Interno) Configura un repo ya inyectado con los labels SSL de Traefik dinámicamente."""
    import yaml
    
    app_dir = APPS_DIR / app_name
    compose_path = app_dir / "docker-compose.yml"
    
    if not compose_path.exists():
        console.print(f"[red]❌ No se encontró docker-compose.yml en la raíz del repositorio ({app_dir})[/red]")
        return
        
    with open(compose_path, "r") as f:
        compose_data = yaml.safe_load(f)
        
    services = compose_data.get("services", {})
    if not services:
        console.print(f"[red]❌ El archivo docker-compose.yml no tiene servicios definidos.[/red]")
        return
        
    svc_names = list(services.keys())
    console.print(f"[bold cyan]Servicios detectados en el repositorio:[/bold cyan] {', '.join(svc_names)}")
    
    target_svc = questionary.select(
        "Elige a qué servicio le enrutaremos el tráfico web público (Traefik SSL):", 
        choices=svc_names
    ).ask()
    
    if not target_svc:
         return
         
    app_port = typer.prompt("Puerto interno EXPOSE sobre el que escucha este contenedor web", type=int, default=80)
    app_domain = typer.prompt("Dominio público definitivo (ej. api.midominio.com)", type=str)
    
    # 1. Inyectar red global
    svc = services[target_svc]
    networks = svc.get("networks", [])
    if isinstance(networks, list) and "boxops-network" not in networks:
        networks.append("boxops-network")
    svc["networks"] = networks
    
    # 2. Inyectar labels Traefik
    labels = svc.get("labels", [])
    if isinstance(labels, dict):
        labels_list = [f"{k}={v}" for k, v in labels.items()]
        labels = labels_list
    if labels is None:
        labels = []
    
    new_labels = [
        "traefik.enable=true",
        f"traefik.http.routers.{app_name}.rule=Host(`{app_domain}`)",
        f"traefik.http.routers.{app_name}.entrypoints=websecure",
        f"traefik.http.routers.{app_name}.tls=true",
        f"traefik.http.routers.{app_name}.tls.certresolver=myresolver",
        f"traefik.http.services.{app_name}.loadbalancer.server.port={app_port}"
    ]
    
    for nl in new_labels:
        if nl not in labels:
            labels.append(nl)
            
    svc["labels"] = labels
    
    # 3. Asegurar red externa global en root
    global_nets = compose_data.get("networks", {})
    if global_nets is None:
        global_nets = {}
    global_nets["boxops-network"] = {"external": True}
    compose_data["networks"] = global_nets
    
    with open(compose_path, "w") as f:
        yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
        
    console.print(f"[bold green]✔ Labels de Proxy dinámico inyectados exitosamente en '{target_svc}'.[/bold green]")
    console.print(f">> Compilando y levantando contenedores de '{app_name}'...")
    
    success, _ = run_command(["docker", "compose", "up", "--build", "-d"], cwd=app_dir)
    if success:
        console.print(f"[bold green]✔ Aplicación '{app_name}' desplegada masivamente en el Servidor.[/bold green]")
        console.print(f"🌍 Disponible (con SSL automático) en: [bold underline]https://{app_domain}[/bold underline]")
        from boxops.utils.telegram import send_telegram_alert
        send_telegram_alert(f"🚢 <b>Push Remoto Exitoso</b>: El Workload <code>{app_name}</code> se transpiló y desplegó en <b>{app_domain}</b> vía rsync.")
    else:
        console.print(f"[bold red]❌ Hubo un error levantando los contenedores de '{app_name}'. Verifica con 'docker compose logs'[/bold red]")
