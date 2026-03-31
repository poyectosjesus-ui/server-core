#!/usr/bin/env bash
# BoxOps - Server Management Bootstrap Script (v1.0.0 MVP)
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
    echo "  ____               ___             "
    echo " |  _ \\             / _ \\            "
    echo " | |_) | _____  ___| | | |_ __  ___  "
    echo " |  _ < / _ \\ \\/ / | | | | '_ \\/ __| "
    echo " | |_) | (_) >  <| |_| | |_) \\__ \\ "
    echo " |____/ \\___/_/\\_\\\\___/| .__/|___/ "
    echo "                       | |           "
    echo "                       |_|           "
    echo -e "${CYAN} --- DevOps Provisioning MVP v1.0.0 ---${NC}"
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
install_boxops() {
    print_banner
    print_info "Iniciando instalación de dependencias..."
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y python3 python3-pip python3-venv curl git ufw fail2ban
        if ! command -v docker &> /dev/null; then
            print_info "Instalando Docker..."
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm -f get-docker.sh
        fi
    else
        print_warning "apt-get no detectado (probablemente estás en macOS o RedHat)."
        print_warning "Solo se configurará el entorno Python local."
        sleep 2
    fi

    print_info "Preparando directorio $INSTALL_DIR..."
    sudo mkdir -p $INSTALL_DIR
    sudo chown -R $USER:$USER $INSTALL_DIR
    cp -r "$REPO_DIR"/* $INSTALL_DIR/ || true

    print_info "Configurando entorno de Python..."
    cd $INSTALL_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
    sudo ln -sf $INSTALL_DIR/venv/bin/boxops /usr/local/bin/boxops

    print_success "¡BoxOps instalado exitosamente en $INSTALL_DIR y disponible globalmente como 'boxops'!"
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

uninstall_boxops() {
    print_banner
    print_warning "Estás a punto de desinstalar BoxOps por completo."
    read -p "¿Estás seguro? (s/n): " confirm
    if [[ "$confirm" == "s" || "$confirm" == "S" ]]; then
        print_info "Eliminando directorio $INSTALL_DIR..."
        sudo rm -rf $INSTALL_DIR
        print_info "Eliminando ejecutable..."
        sudo rm -f /usr/local/bin/boxops
        print_success "Desinstalación completada."
    else
        print_info "Operación cancelada."
    fi
    read -p "Presiona ENTER para continuar..."
}

# ==========================================
# Main Menu Loop
# ==========================================
while true; do
    print_banner
    echo -e "${BOLD}Opciones Disponibles:${NC}"
    echo "  1) 🚀 Instalar / Refrescar BoxOps"
    echo "  2) 🔄 Actualizar Código (Git Pull)"
    echo "  3) 🗑️  Desinstalar BoxOps"
    echo "  4) 👋 Salir"
    echo ""
    read -p "Selecciona una opción [1-4]: " option

    case $option in
        1) install_boxops ;;
        2) update_boxops ;;
        3) uninstall_boxops ;;
        4) 
            print_success "¡Hasta pronto!"
            exit 0
            ;;
        *) 
            print_error "Opción no válida. Inténtalo de nuevo."
            sleep 2
            ;;
    esac
done
