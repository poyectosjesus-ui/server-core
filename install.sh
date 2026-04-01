#!/usr/bin/env bash
# BoxOps - Server Management Bootstrap Script (v1.1.0 Provisioning MVP)
set -e

# ==========================================
# Colors & Styles
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ==========================================
# Helper Functions
# ==========================================
print_info() { echo -e "${CYAN}ℹ️  ${1}${NC}"; }
print_success() { echo -e "${GREEN}✅ ${1}${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  ${1}${NC}"; }
print_error() { echo -e "${RED}❌ ${1}${NC}"; }

print_banner() {
    clear
    echo -e "${BLUE}${BOLD}"
    echo " ╭───────────────────────────────────────────────╮"
    echo " │                                               │"
    echo " │     ____               ___                    │"
    echo " │    |  _ \\             / _ \\                   │"
    echo " │    | |_) | _____  ___| | | |_ __  ___         │"
    echo " │    |  _ < / _ \\ \\/ / | | | | '_ \\/ __|        │"
    echo " │    | |_) | (_) >  <| |_| | |_) \\__ \\        │"
    echo " │    |____/ \\___/_/\\_\\\\___/| .__/|___/        │"
    echo " │                          | |                  │"
    echo " │                          |_|                  │"
    echo " │                                               │"
    echo " │    ${CYAN}--- DevOps Provisioning MVP v1.0.1 --${BLUE}    │"
    echo " ╰───────────────────────────────────────────────╯${NC}"
    echo ""
}

# ==========================================
# Application Settings
# ==========================================
INSTALL_DIR="/opt/boxops"
REPO_DIR=$(pwd)

# ==========================================
# Core Functions
# ==========================================

provision_server() {
    print_banner
    print_info "Iniciando aprovisionamiento del servidor base..."
    
    if command -v apt-get &> /dev/null; then
        print_info "Actualizando repositorios y Sistema Operativo..."
        sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
        sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
        
        print_info "Instalando dependencias base y seguridad (ufw, fail2ban)..."
        sudo DEBIAN_FRONTEND=noninteractive apt-get install -y curl git ufw fail2ban python3 python3-pip python3-venv apt-transport-https ca-certificates software-properties-common
        
        if ! command -v docker &> /dev/null; then
            print_info "Instalando Docker Engine y Docker Compose..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm -f get-docker.sh
        else
            print_success "Docker ya está instalado."
        fi
        
        print_info "Configurando Firewall (UFW)..."
        sudo ufw default deny incoming
        sudo ufw default allow outgoing
        sudo ufw allow ssh
        sudo ufw allow http
        sudo ufw allow https
        # Habilitar UFW (requiere 'yes' en caso de que pregunte si desconectará SSH)
        sudo ufw --force enable || true

        print_success "Aprovisionamiento del servidor completado con éxito."
    else
        print_warning "apt-get no detectado (probablemente estás en macOS o RedHat)."
        print_warning "El aprovisionamiento de SO está diseñado para Debian/Ubuntu."
        sleep 2
    fi
    echo ""
    read -p "Presiona ENTER para continuar..."
}

install_boxops() {
    print_banner
    print_info "Preparando CLI de BoxOps en $INSTALL_DIR..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 no está instalado. Por favor ejecuta 'Aprovisionar Servidor Base' primero."
        read -p "Presiona ENTER para continuar..."
        return
    fi

    sudo mkdir -p $INSTALL_DIR
    sudo chown -R $USER:$user $INSTALL_DIR
    
    if [ ! -f "$REPO_DIR/boxops/main.py" ]; then
        print_info "Dependencias Locales no encontradas. Descargando BoxOps Edge desde GitHub..."
        sudo git clone https://github.com/poyectosjesus-ui/server-core.git /tmp/boxops-clone
        sudo cp -r /tmp/boxops-clone/* $INSTALL_DIR/
        sudo rm -rf /tmp/boxops-clone
    else
        sudo cp -r "$REPO_DIR"/* $INSTALL_DIR/ || true
    fi

    print_info "Configurando entorno de Python virtual..."
    cd $INSTALL_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    sudo ln -sf $INSTALL_DIR/venv/bin/boxops /usr/local/bin/boxops

    print_success "¡CLI de BoxOps instalada exitosamente!"
    print_success "Disponible globalmente como el comando 'boxops'."
    echo ""
    
    if [ -t 0 ]; then
        read -p "Presiona ENTER para continuar..."
    fi
}

verify_status() {
    print_banner
    print_info "Verificando estado de las dependencias base..."
    echo ""
    
    # Función auxiliar para comprobar estado con systemd
    check_service() {
        if systemctl is-active --quiet "$1"; then
            echo -e "${GREEN}✅ $1 está ACTIVO y ejecutándose.${NC}"
        else
            echo -e "${RED}❌ $1 NO ESTÁ ACTIVO.${NC}"
        fi
    }

    echo -e "${BOLD}--- Estado de Servicios (Systemd) ---${NC}"
    if command -v systemctl &> /dev/null; then
        check_service "docker"
        check_service "ufw"
        check_service "fail2ban"
    else
        print_warning "systemctl no disponible (entorno no-Linux o macOS)."
    fi

    echo ""
    echo -e "${BOLD}--- Estado de Binarios ---${NC}"
    
    check_bin() {
        if command -v "$1" &> /dev/null; then
            echo -e "${GREEN}✅ $1 existe en: $(which $1)${NC}"
        else
            echo -e "${RED}❌ $1 NO encontrado.${NC}"
        fi
    }

    check_bin "docker"
    check_bin "ufw"
    check_bin "fail2ban-server"
    check_bin "python3"
    check_bin "git"
    check_bin "boxops"

    echo ""
    read -p "Presiona ENTER para continuar..."
}

update_boxops() {
    print_banner
    print_info "Comprobando actualizaciones de BoxOps..."
    if [ ! -d "$INSTALL_DIR" ]; then
        print_error "BoxOps no está instalado en $INSTALL_DIR"
        read -p "Presiona ENTER para continuar..."
        return
    fi

    cd $INSTALL_DIR
    print_info "Actualizando código fuente..."
    if [ -d ".git" ]; then
        git pull origin main || print_warning "No se pudo actualizar desde git. Continuaremos con la instalación local."
    else
        print_warning "El directorio no es un repositorio git. No se harán cambios remotos."
    fi
    
    print_info "Actualizando dependencias..."
    source venv/bin/activate
    pip install -e .
    
    print_success "¡BoxOps actualizado correctamente!"
    read -p "Presiona ENTER para continuar..."
}

master_setup_wizard() {
    print_banner
    print_info "=========================================================="
    print_info "🚀 INICIANDO ASISTENTE MAESTRO DE BOXOPS SETUP 🚀"
    print_info "=========================================================="
    echo ""
    
    # 1. OS Provisioning & Security
    print_info "Paso 1/3: Preparando el Sistema Operativo y Seguridad..."
    if command -v docker &> /dev/null && command -v ufw &> /dev/null; then
        print_success "El SO base y utilidades principales ya están instalados."
    else
        provision_server
    fi
    
    # 2. BoxOps CLI Install
    echo ""
    print_info "Paso 2/3: Instalando / Actualizando BoxOps CLI..."
    install_boxops
    
    # 3. Infrastructure Launch via Python
    echo ""
    print_info "Paso 3/3: Despliegue de Infraestructura Core..."
    if command -v boxops &> /dev/null; then
        sudo /usr/local/bin/boxops infra wizard
    else
        print_error "La CLI de BoxOps falló en instalarse. No podemos ejecutar el Wizard de Infraestructura."
    fi
    
    echo ""
    print_success "Asistente Maestro finalizado correctamente."
    read -p "Presiona ENTER para volver al menú principal..."
}

uninstall_boxops() {
    print_banner
    print_warning "Estás a punto de desinstalar la CLI local BoxOps."
    print_warning "NOTA: Esto no desinstalará Docker, UFW ni Fail2ban."
    read -p "¿Estás seguro? (s/n): " confirm
    if [[ "$confirm" == "s" || "$confirm" == "S" ]]; then
        print_info "Eliminando directorio $INSTALL_DIR..."
        sudo rm -rf $INSTALL_DIR
        print_info "Eliminando ejecutable..."
        sudo rm -f /usr/local/bin/boxops
        print_success "Desinstalación de la CLI completada."
    else
        print_info "Operación cancelada."
    fi
    read -p "Presiona ENTER para continuar..."
}

# ==========================================
# Main Executable Logic
# ==========================================

# If not running in a TTY (e.g. piped from curl), bypass menu and run sequential setup natively:
if [ ! -t 0 ]; then
    print_banner
    print_info "Detectada instalación no interactiva (Piped vía Curl)."
    
    # 1. Instalar OS Dependencies Auto
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -y
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y curl git ufw fail2ban python3 python3-pip python3-venv apt-transport-https ca-certificates software-properties-common
    
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        rm -f get-docker.sh
    fi
    
    # 2. Download and Link BoxOps
    install_boxops
    
    echo ""
    print_success "¡Instalación base completada automáticamente!"
    print_info "NOTA: Para configurar la Infraestructura interactiva, ejecuta ahora mismo en tu consola:"
    echo -e "${YELLOW}>> sudo boxops infra wizard${NC}"
    echo ""
    exit 0
fi

# Standard Interactive Menu Fallback
while true; do
    print_banner
    echo -e "${BOLD}${CYAN} ╭─[ MENÚ PRINCIPAL DE INSTALACIÓN ]────────────╮${NC}"
    echo -e "${CYAN} │${NC}                                              ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}  ${BOLD}1)${NC} 🚀 BoxOps Setup Wizard (Asistente Maestro) ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}  ${BOLD}2)${NC} 📊 Server Status & Monitoring              ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}  ${BOLD}3)${NC} 🔄 Forzar Actualización (Git Pull)         ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}  ${BOLD}4)${NC} 🗑️  Desinstalar BoxOps de Este Servidor     ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}  ${BOLD}5)${NC} 👋 Salir                                   ${CYAN}│${NC}"
    echo -e "${CYAN} │${NC}                                              ${CYAN}│${NC}"
    echo -e "${BOLD}${CYAN} ╰──────────────────────────────────────────────╯${NC}"
    echo ""
    read -p "$(echo -e ${BOLD}Selecciona una opción [1-5]: ${NC})" option

    case $option in
        1) master_setup_wizard ;;
        2) verify_status ;;
        3) update_boxops ;;
        4) uninstall_boxops ;;
        5) 
            print_success "¡Hasta pronto! Ejecuta 'boxops' en la terminal en cualquier momento."
            exit 0
            ;;
        *) 
            print_error "Opción no válida. Inténtalo de nuevo."
            sleep 1
            ;;
    esac
done
