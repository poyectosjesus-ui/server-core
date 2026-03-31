#!/usr/bin/env bash
# BoxOps - Server Management Bootstrap Script (v1.0.0 MVP)
set -e

echo "🚀 Iniciando Instalación de Servidor V1.0.0 MVP"
INSTALL_DIR="/opt/boxops"
REPO_DIR=$(pwd)

if command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-pip python3-venv curl git ufw fail2ban
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
fi

sudo mkdir -p $INSTALL_DIR
sudo chown -R $USER:$USER $INSTALL_DIR
cp -r "$REPO_DIR"/* $INSTALL_DIR/ || true

cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install -e .
sudo ln -sf $INSTALL_DIR/venv/bin/boxops /usr/local/bin/boxops

echo "✅ ¡Instalación completada exitosamente!"
