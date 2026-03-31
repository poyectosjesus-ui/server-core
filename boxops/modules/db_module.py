import subprocess
import secrets
import string
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import Optional

app = typer.Typer(help="Gestión Avanzada de Bases de Datos (Instancias dedicadas y BD lógicas aisladas)")
console = Console()

INFRA_DIR = Path("/opt/boxops/infra")

def run_command(cmd_list: list, cwd: Optional[Path] = None, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run(cmd_list, check=True, cwd=cwd, capture_output=True, text=True)
            return True, result.stdout
        else:
            subprocess.run(cmd_list, check=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if capture_output else ""

def generate_strong_password(length=16):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password

def get_postgres_users(host: str, admin_user: str) -> list:
    success, out = run_command(["docker", "exec", "-i", host, "psql", "-U", admin_user, "-tAc", "SELECT usename FROM pg_user;"], capture_output=True)
    if success:
        return [u.strip() for u in out.split('\\n') if u.strip()]
    return []

def get_mysql_users(host: str, admin_user: str, admin_pass: str) -> list:
    success, out = run_command(["docker", "exec", "-i", host, "mysql", "-u", admin_user, f"-p{admin_pass}", "-e", "SELECT user FROM mysql.user;"], capture_output=True)
    if success:
        lines = out.split('\\n')
        # skip header 'user'
        if len(lines) > 1:
            return [u.strip() for u in lines[1:] if u.strip()]
    return []

@app.command("wizard")
def db_wizard():
    """Asistente paso a paso para crear de forma segura una BD lógica y Aislar Credenciales."""
    console.print(Panel.fit("[bold bright_blue]🧙‍♂️ Asistente DBA BoxOps[/bold bright_blue]\nAprovisionamiento Aislado de Bases de Datos", border_style="cyan"))
    
    # 1. Seleccionar Host y Motor
    host = typer.prompt("¿Cuál es el contenedor host de tu base de datos global?", default="boxops-postgres")
    success, _ = run_command(["docker", "inspect", host], capture_output=True)
    if not success:
        console.print(f"[bold red]❌ El contenedor '{host}' no está corriendo en Docker.[/bold red]")
        return
        
    engine = typer.prompt("¿Qué motor de base de datos es? (postgres / mysql)", default="postgres").lower()
    
    admin_user = typer.prompt(f"Usuario root/admin del contenedor {host}", default=("postgres" if engine=="postgres" else "root"))
    
    admin_pass = ""
    if engine == "mysql":
        admin_pass = typer.prompt("Contraseña admin maestro (para ejecutar comandos)", hide_input=True)

    # 2. Detalles de la BD
    db_name = typer.prompt("\n👉 ¿Cómo se llamará la nueva base de datos lógica?")
    
    # Listar usuarios existentes para decidir
    existing_users = []
    console.print("\n[dim]Consultando usuarios existentes...[/dim]")
    if engine == "postgres":
        existing_users = get_postgres_users(host, admin_user)
    elif engine == "mysql":
        existing_users = get_mysql_users(host, admin_user, admin_pass)
        
    if existing_users:
        console.print("[cyan]Usuarios existentes en la instancia:[/cyan] " + ", ".join(existing_users))
    
    # 3. Usuario de la DB
    use_existing = False
    if existing_users:
        use_existing = typer.confirm("¿Deseas asignar/reusar un usuario existente en lugar de crear uno nuevo?", default=False)
        
    db_user = ""
    db_pass = ""
    
    if use_existing:
        db_user = typer.prompt("Escribe el nombre del usuario existente que tendrá acceso")
        if db_user not in existing_users:
            console.print(f"[red]⚠️ El usuario '{db_user}' no fue detectado, pero intentaremos continuar.[/red]")
    else:
        db_user = typer.prompt("👉 ¿Cómo se llamará el NUEVO usuario aislado?")
        gen_pass = typer.confirm("¿Deseas que BoxOps genere una contraseña fuerte y segura automáticamente?", default=True)
        if gen_pass:
            db_pass = generate_strong_password()
            console.print(f"[bold green]✔ Contraseña generada automáticamente.[/bold green]")
        else:
            db_pass = typer.prompt("Introduce la contraseña para este nuevo usuario", hide_input=True)

    # 4. Confirmación
    console.print("\n[bold yellow]Resumen de la Operación:[/bold yellow]")
    table = Table(show_header=False, box=None)
    table.add_row("Contenedor Host:", host)
    table.add_row("Motor DB:", engine)
    table.add_row("Nueva Base de Datos:", f"[bold green]{db_name}[/bold green]")
    table.add_row("Usuario Asignado:", f"[bold cyan]{db_user}[/bold cyan] ({'Existente' if use_existing else 'Nuevo'})")
    console.print(table)
    
    confirm = typer.confirm("\n¿Ejecutar la creación en la base de datos ahora?", default=True)
    if not confirm:
        console.print("[yellow]Operación cancelada por el usuario.[/yellow]")
        return
        
    console.print(f"\n>> Ejecutando consultas SQL en {host}...", end=" ")
    
    # 5. Ejecución
    if engine == "postgres":
        queries = [f"CREATE DATABASE {db_name};"]
        if not use_existing:
            queries.append(f"CREATE USER {db_user} WITH ENCRYPTED PASSWORD '{db_pass}';")
        queries.extend([
            f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};",
            f"ALTER DATABASE {db_name} OWNER TO {db_user};"
        ])
        
        for q in queries:
            success, err = run_command(["docker", "exec", "-i", host, "psql", "-U", admin_user, "-c", q], capture_output=True)
            if not success and "already exists" not in err.lower():
                console.print(f"\n[red]Error SQL: {err}[/red]")
                
    elif engine == "mysql":
        queries = [f"CREATE DATABASE IF NOT EXISTS {db_name};"]
        if not use_existing:
            queries.append(f"CREATE USER IF NOT EXISTS '{db_user}'@'%' IDENTIFIED BY '{db_pass}';")
        queries.extend([
            f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{db_user}'@'%';",
            "FLUSH PRIVILEGES;"
        ])
        
        for q in queries:
            success, err = run_command(["docker", "exec", "-i", host, "mysql", "-u", admin_user, f"-p{admin_pass}", "-e", q], capture_output=True)
            if not success:
                console.print(f"\n[red]Error SQL: {err}[/red]")
    
    console.print("[green]✔ Hecho[/green]")

    # 6. Salida de Configuración Lista para Usar
    console.print("\n" + "="*50)
    console.print("[bold bright_green]🚀 ¡Base de Datos Aislada Lista![/bold bright_green]")
    console.print("="*50)
    console.print("\nCopia y pega la siguiente URL de conexión (Connection String) en el `.env` de tu aplicación:\n")
    
    host_ip_or_name = "127.0.0.1" # o el nombre del contenedor si está en la misma red de docker
    port = "5432" if engine == "postgres" else "3306"
    
    # Connection string
    if not use_existing:
        conn_str = f"{engine}://{db_user}:{db_pass}@{host}:{port}/{db_name}"
        console.print(Panel(f"[bold white]{conn_str}[/bold white]", title="Connection URL", border_style="green"))
        
        console.print("\n[bold yellow]⚠️ Guarda la contraseña generada, no se volverá a mostrar:[/bold yellow]")
        console.print(f"Password: [bold white]{db_pass}[/bold white]\n")
    else:
        conn_str = f"{engine}://{db_user}:<LA_CONTRASEÑA_EXISTENTE>@{host}:{port}/{db_name}"
        console.print(Panel(f"[bold white]{conn_str}[/bold white]", title="Connection URL", border_style="green"))
        
    console.print("[dim]Nota: Si la aplicación corre en 'boxops-network', reemplaza '127.0.0.1' por el nombre del contenedor host ('{host}').[/dim]\n")


@app.command("create-instance")
def create_instance(
    name: str = typer.Argument(..., help="Nombre del contenedor (ej: boxops-db-ventas)"),
    type: str = typer.Option("postgres", "--type", help="Motor: postgres o mysql"),
    port: int = typer.Option(5432, "--port", help="Puerto local expuesto en el host")
):
    """Crea un contenedor de Base de Datos completamente DEDICADO."""
    console.print(f"[bold cyan]Aprovisionando Instancia Dedicada: {name} ({type})[/bold cyan]")
    
    db_user = typer.prompt("Usuario administrador de esta instancia", default="admin")
    db_pass = typer.prompt("Contraseña admin", hide_input=True)
    db_name = typer.prompt("Nombre de BD inicial", default="appdb")
    
    instance_dir = INFRA_DIR / f"database_{name}"
    instance_dir.mkdir(parents=True, exist_ok=True)
    
    if type.lower() == "postgres":
        compose_content = f"""version: "3.8"
services:
  {name}:
    image: postgres:15
    container_name: {name}
    restart: unless-stopped
    environment:
      POSTGRES_USER: {db_user}
      POSTGRES_PASSWORD: {db_pass}
      POSTGRES_DB: {db_name}
    ports:
      - "{port}:5432"
    volumes:
      - {name}-data:/var/lib/postgresql/data
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  {name}-data:
"""
    elif type.lower() == "mysql":
        compose_content = f"""version: "3.8"
services:
  {name}:
    image: mysql:8
    container_name: {name}
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: {db_pass}
      MYSQL_USER: {db_user}
      MYSQL_PASSWORD: {db_pass}
      MYSQL_DATABASE: {db_name}
    ports:
      - "{port}:3306"
    volumes:
      - {name}-data:/var/lib/mysql
    networks:
      - boxops-network

networks:
  boxops-network:
    external: true
volumes:
  {name}-data:
"""
    else:
        console.print("[red]Tipo de DB no soportado. Usa 'postgres' o 'mysql'.[/red]")
        return
        
    (instance_dir / "docker-compose.yml").write_text(compose_content)
    
    console.print(f">> Levantando contenedor {name}...")
    success, _ = run_command(["docker", "compose", "up", "-d"], cwd=instance_dir)
    if success:
        console.print(f"[bold green]✔ Instancia dedicada '{name}' lista en el puerto local {port}.[/bold green]")
    else:
        console.print(f"[red]❌ Error originado en docker daemon levantando instancia {name}.[/red]")
