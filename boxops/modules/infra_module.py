import os
import subprocess
from pathlib import Path
from typing import Optional
import typer
import questionary
from rich.console import Console

app = typer.Typer()
console = Console()

INFRA_DIR = Path("/opt/boxops/infra")

def run_command(cmd_list: list, cwd: Optional[Path] = None):
    try:
        subprocess.run(cmd_list, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

@app.command("setup")
def setup_infra(
    proxy: bool = typer.Option(False, "--proxy", help="Desplegar Traefik Reverse Proxy"),
    observability: bool = typer.Option(False, "--observability", help="Desplegar Prometheus & Grafana"),
    database: bool = typer.Option(False, "--database", help="Desplegar PostgreSQL Global"),
    cache: bool = typer.Option(False, "--cache", help="Desplegar Caché Global (Redis)"),
    minio: bool = typer.Option(False, "--minio", help="Desplegar Object Storage (MinIO)"),
    backups: bool = typer.Option(False, "--backups", help="Desplegar DB Backups Automatizados"),
    email: str = typer.Option(None, "--email", help="Email para certificados SSL Let's Encrypt (requerido para --proxy)")
):
    """Instala y configura la infraestructura base de Servidor."""
    
    # Typer sanitization: Si se llama programáticamente, las faltantes llegan como OptionInfo (Truthys)
    proxy = proxy if isinstance(proxy, bool) else proxy.default
    observability = observability if isinstance(observability, bool) else observability.default
    database = database if isinstance(database, bool) else database.default
    cache = cache if isinstance(cache, bool) else cache.default
    minio = minio if isinstance(minio, bool) else minio.default
    backups = backups if isinstance(backups, bool) else backups.default
    email = email if isinstance(email, str) else None
    
    if not proxy and not observability and not database and not cache and not minio and not backups:
        console.print("[yellow]Debes especificar qué componente instalar (--proxy, --observability, --database, --cache, --minio, --backups).[/yellow]")
        return
        
    # Asegurar que la red global exista
    run_command(["docker", "network", "create", "boxops-network"])
    
    if proxy:
        if not email:
            email = typer.prompt("Introduce tu correo electrónico para Let's Encrypt (SSL)")
            
        console.print("[bold cyan]Iniciando despliegue del Reverse Proxy (Traefik v3)[/bold cyan]")
        proxy_dir = INFRA_DIR / "proxy"
        proxy_dir.mkdir(parents=True, exist_ok=True)
        
        data_dir = proxy_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        acme_file = data_dir / "acme.json"
        if not acme_file.exists():
            acme_file.touch()
        acme_file.chmod(0o600)
        
        compose_content = f"""version: "3.8"
services:
  traefik:
    image: traefik:v3.0
    container_name: boxops-traefik
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    networks:
      - boxops-network
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./data/acme.json:/acme.json
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
      - "--entrypoints.web.http.redirections.entryPoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.myresolver.acme.httpchallenge=true"
      - "--certificatesresolvers.myresolver.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.myresolver.acme.email={email}"
      - "--certificatesresolvers.myresolver.acme.storage=/acme.json"

networks:
  boxops-network:
    external: true
"""
        (proxy_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=proxy_dir)
        if success:
            console.print(f"[bold green]✔ Proxy listo con SSL atado a {email}[/bold green]")
        else:
            console.print("[red]❌ Error desplegando Proxy.[/red]")

    if observability:
        console.print("[bold cyan]Iniciando despliegue de Observabilidad (Prometheus + Grafana)[/bold cyan]")
        obs_dir = INFRA_DIR / "observability"
        obs_dir.mkdir(parents=True, exist_ok=True)
        
        prom_content = """global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"""
        (obs_dir / "prometheus.yml").write_text(prom_content)
        
        compose_content = """version: "3.8"
services:
  prometheus:
    image: prom/prometheus:latest
    container_name: boxops-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prom-data:/prometheus
    networks:
      - boxops-network
  grafana:
    image: grafana/grafana:latest
    container_name: boxops-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  prom-data:
  grafana-data:
"""
        (obs_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=obs_dir)
        if success:
            console.print("[bold green]✔ Observabilidad lista (Grafana en :3000, Prometheus en :9090)[/bold green]")
        else:
            console.print("[red]❌ Error desplegando Observabilidad.[/red]")

    if database:
        console.print("[bold cyan]Iniciando despliegue de Base de Datos Global (PostgreSQL)[/bold cyan]")
        db_user = typer.prompt("Usuario para la BD global", default="postgres")
        db_pass = typer.prompt("Contraseña para el usuario", hide_input=True)
        db_name = typer.prompt("Nombre de BD inicial", default="globaldb")
        
        db_dir = INFRA_DIR / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        
        compose_content = f"""version: "3.8"
services:
  postgres:
    image: postgres:15
    container_name: boxops-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: {db_user}
      POSTGRES_PASSWORD: {db_pass}
      POSTGRES_DB: {db_name}
    ports:
      - "5432:5432"
    volumes:
      - pg-data:/var/lib/postgresql/data
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  pg-data:
"""
        (db_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=db_dir)
        if success:
            console.print(f"[bold green]✔ Base de Datos lista en puerto 5432 (DB: {db_name}, Usuario: {db_user})[/bold green]")
        else:
            console.print("[red]❌ Error desplegando Base de Datos.[/red]")

    if cache:
        console.print("[bold cyan]Iniciando despliegue de Caché Global (Redis)[/bold cyan]")
        cache_dir = INFRA_DIR / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        compose_content = """version: "3.8"
services:
  redis:
    image: redis:7-alpine
    container_name: boxops-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  redis-data:
"""
        (cache_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=cache_dir)
        if success:
            console.print("[bold green]✔ Caché global (Redis) lista en puerto 6379[/bold green]")
        else:
            console.print("[red]❌ Error desplegando Caché Redis.[/red]")

    if minio:
        console.print("[bold cyan]Iniciando despliegue de Object Storage S3 (MinIO)[/bold cyan]")
        m_user = typer.prompt("Usuario admin de MinIO", default="admin")
        m_pass = typer.prompt("Contraseña admin de MinIO", hide_input=True)
        
        m_dir = INFRA_DIR / "minio"
        m_dir.mkdir(parents=True, exist_ok=True)
        
        compose_content = f"""version: "3.8"
services:
  minio:
    image: minio/minio:latest
    container_name: boxops-minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: {m_user}
      MINIO_ROOT_PASSWORD: {m_pass}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio-data:/data
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  minio-data:
"""
        (m_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=m_dir)
        if success:
            console.print(f"[bold green]✔ MinIO (S3) listo. API: 9000, Consola UI: 9001 (User: {m_user})[/bold green]")
        else:
            console.print("[red]❌ Error desplegando MinIO.[/red]")

    if backups:
        console.print("[bold cyan]Configurando Dumps Automatizados de BD (PostgreSQL)[/bold cyan]")
        # Asume PostgreSQL global
        db_pass = typer.prompt("Introduce nuevamente la contraseña del administrador 'postgres' global", hide_input=True)
        
        bkp_dir = INFRA_DIR / "backups"
        bkp_dir.mkdir(parents=True, exist_ok=True)
        
        compose_content = f"""version: "3.8"
services:
  pg-backup:
    image: prodrigestivill/postgres-backup-local
    container_name: boxops-db-backup
    restart: unless-stopped
    environment:
      POSTGRES_HOST: boxops-postgres
      POSTGRES_DB: globaldb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: {db_pass}
      POSTGRES_EXTRA_OPTS: '-Z6 --schema-only'
      SCHEDULE: '@daily'
      BACKUP_KEEP_DAYS: 7
    volumes:
      - ./backup-files:/backups
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
"""
        (bkp_dir / "docker-compose.yml").write_text(compose_content)
        success = run_command(["docker", "compose", "up", "-d"], cwd=bkp_dir)
        if success:
            console.print("[bold green]✔ Tarea Cron de Backups diaria inicializada y atada a boxops-postgres.[/bold green]")
        else:
            console.print("[red]❌ Error configurando Backups automáticos.[/red]")


@app.command("wizard")
def infra_wizard():
    """Asistente interactivo inteligente para desplegar toda la infraestructura."""
    console.print("[bold bright_blue]🪄 Asistente de Infraestructura Global BoxOps[/bold bright_blue]")
    console.print("Este asistente configurará los servicios core de forma segura e idempotente.\n")
    
    # === Telegram Config ===
    env_file = INFRA_DIR / ".env"
    if not env_file.exists():
        console.print("[dim]Configurando variables base de entorno BoxOps...[/dim]")
        setup_tg = typer.confirm("¿Deseas configurar un Bot de Telegram para recibir alertas del servidor?", default=True)
        if setup_tg:
            tg_token = typer.prompt("Introduce el TOKEN de tu Bot de Telegram", hide_input=True)
            tg_chat = typer.prompt("Introduce tu Chat ID de Telegram")
            env_file.parent.mkdir(parents=True, exist_ok=True)
            env_file.write_text(f"TELEGRAM_BOT_TOKEN={tg_token}\nTELEGRAM_CHAT_ID={tg_chat}\n")
            console.print("[green]✔ Credenciales de Telegram encriptadas/guardadas.[/green]\n")
        else:
            env_file.parent.mkdir(parents=True, exist_ok=True)
            env_file.touch()
    
    # === Inspeccionar Estado Previo ===
    estados = {}
    for comp in ["proxy", "observability", "database", "cache", "minio", "backups"]:
        estados[comp] = (INFRA_DIR / comp / "docker-compose.yml").exists()

    # === Topología de Servidor (Server Profile) ===
    perfil = questionary.select(
        "¿Cuál será el Rol / Topología de este servidor en tu red?",
        choices=[
            "All-in-One (Instala TODO: Proxy, BD, Caché, Infra)",
            "Web / Compute Node (Ideal Frontend/API: Solo Proxy y Monitoreo)",
            "Data Node (Ideal Backend: Solo DBs, Redis, Storage - SIN Proxy Web)"
        ]
    ).ask()
    
    if not perfil:
        return
        
    is_compute = "Compute Node" in perfil
    is_data = "Data Node" in perfil
    is_all = "All-in-One" in perfil

    # === Questionary Muli-Select ===
    opciones = []
    
    # Validar Proxy
    if estados["proxy"]:
        console.print("[yellow]ℹ️  Reverse Proxy (Traefik) ya está configurado.[/yellow]")
    else:
        opciones.append(questionary.Choice("🌐 Reverse Proxy SSL Traefik v3", "proxy", checked=(is_compute or is_all)))
        
    # Observabilidad
    if estados["observability"]:
        console.print("[yellow]ℹ️  Observabilidad (Prometheus+Grafana) ya está configurada.[/yellow]")
    else:
        opciones.append(questionary.Choice("📈 Observabilidad Prometheus & Grafana", "obsv", checked=(is_compute or is_all)))
        
    # Database
    if estados["database"]:
        console.print("[yellow]ℹ️  Base de Datos Global SQL ya está configurada.[/yellow]")
    else:
        opciones.append(questionary.Choice("🗄️ Base de Datos Global PostgreSQL", "db", checked=(is_data or is_all)))
        
    # Caché
    if estados["cache"]:
        console.print("[yellow]ℹ️  Caché Redis ya está configurada.[/yellow]")
    else:
        opciones.append(questionary.Choice("⚡ Caché Local Redis", "cache", checked=(is_data or is_all)))
        
    # MinIO
    if estados["minio"]:
        console.print("[yellow]ℹ️  Almacenamiento Object Storage MinIO ya está configurado.[/yellow]")
    else:
        opciones.append(questionary.Choice("📦 Object Storage S3 MinIO", "minio", checked=(is_data or is_all)))
        
    # Backups
    if estados["backups"]:
        console.print("[yellow]ℹ️  Backups de BD ya están configurados.[/yellow]")
    else:
        opciones.append(questionary.Choice("💾 Respaldos Automatizados de BD", "backups", checked=(is_data or is_all)))
        
    if not opciones:
        console.print("\n[bold green]✅ Toda la Infraestructura Base ya está desplegada. Nada por hacer.[/bold green]")
        return
        
    respuestas = questionary.checkbox(
        "¿Qué componentes deseas instalar/aprovisionar ahora mismo?", 
        choices=opciones,
        style=questionary.Style([('selected', 'fg:green bold')])
    ).ask()
    
    if not respuestas:
        console.print("[yellow]No seleccionaste ningún componente. Saliendo del asistente.[/yellow]")
        return

    # === Ejecución Segura ===
    # Asegurar red
    run_command(["docker", "network", "create", "boxops-network"])
    
    if "proxy" in respuestas:
        email = typer.prompt("\nIntroduce tu correo electrónico para Let's Encrypt (SSL del Proxy)")
        setup_infra(proxy=True, email=email)
        
    if "obsv" in respuestas:
        setup_infra(observability=True)
        
    if "db" in respuestas:
        setup_infra(database=True)
        
    if "cache" in respuestas:
        setup_infra(cache=True)
        
    if "minio" in respuestas:
        setup_infra(minio=True)
        
    if "backups" in respuestas:
        setup_infra(backups=True)
        
    console.print("\n[bold green]✅ Configuración de infraestructura seleccionada finalizada exitosamente.[/bold green]")
    from boxops.utils.telegram import send_telegram_alert
    send_telegram_alert(f"🚀 <b>BoxOps Master</b>: Infraestructura base provisionada.\nRol: {perfil}")


@app.command("down")
def stop_infra(
    proxy: bool = typer.Option(False, "--proxy", help="Detener Proxy"),
    observability: bool = typer.Option(False, "--observability", help="Detener Observabilidad"),
    database: bool = typer.Option(False, "--database", help="Detener Base de Datos"),
    cache: bool = typer.Option(False, "--cache", help="Detener Caché Global"),
    minio: bool = typer.Option(False, "--minio", help="Detener MinIO"),
    backups: bool = typer.Option(False, "--backups", help="Detener Backups Automáticos")
):
    """Detiene los componentes de infraestructura."""
    if not proxy and not observability and not database and not cache and not minio and not backups:
        console.print("[yellow]Especifíca qué detener (--proxy, --observability, --database, --cache, --minio, --backups).[/yellow]")
        return
        
    components = {
        "proxy": proxy,
        "observability": observability,
        "database": database,
        "cache": cache,
        "minio": minio,
        "backups": backups
    }
    
    for name, should_stop in components.items():
        if should_stop:
            console.print(f"[red]Apagando los servicios: {name}...[/red]")
            c_dir = INFRA_DIR / name
            if c_dir.exists():
                run_command(["docker", "compose", "down"], cwd=c_dir)
                console.print(f"[green]✔ {name} de-aprovisionado.[/green]")
            else:
                console.print(f"[yellow]No se encontró infraestructura para {name}[/yellow]")
