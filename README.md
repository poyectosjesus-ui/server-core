# 📦 BoxOps CLI

![Version](https://img.shields.io/badge/version-1.0.0--mvp-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

BoxOps es una herramienta CLI premium construida en Python (`Typer` + `Rich`) diseñada exclusivamente para simplificar y automatizar el aprovisionamiento, la seguridad y la gestión de servidores Linux de grado producción.

## 🚀 Características (Roadmap del Proyecto)
- **Instalación Cero-Fricción (Bootstrap):** Un comando para convertir una máquina Ubuntu/Debian "virgen" en un servidor de despliegues.
- **Proxy Inverso Dinámico:** Despliegue automático de Traefik y gestión inteligente de certificados SSL.
- **Monitoreo Avanzado:** Stack completo con Prometheus, Grafana, Node Exporter y cAdvisor.
- **Seguridad Activa:** Configuración inteligente de Firewalls (UFW), Fail2ban y alertas directas vía Telegram.
- **Gestión de Entornos:** Montaje y desmontaje seguro de contenedores genéricos preconfigurados.
- **Gestor de Respaldos:** Lógicas seguras para crear snapshots (tar.gz) locales de volúmenes de Docker y envíos remotos.

## 💿 Probando el MVP (Fase 1)
Clona el proyecto o sube los archivos a tu servidor Debian/Ubuntu con permisos root y ejecuta:

```bash
chmod +x install.sh
./install.sh
```

El script maestro se encargará de:
1. Instalar Python 3 y `venv`.
2. Instalar Docker, Docker Compose y herramientas básicas de SO.
3. Crear un enlace global para el CLI `boxops`.

Prueba tu instalación desde cualquier ruta en el servidor:
```bash
boxops --help
```

## 🛠️ Arquitectura
- **Núcleo CLI:** Python con las librerías `Typer` (Google CLI) y `Rich` (Formatos UI).
- **Módulos:** BoxOps está estructurado bajo `boxops/modules/`, lo cual permite escalar comandos de forma vertical.
- **Agentes IA:** El desarrollo del código subyacente está guiado por perfiles de Agentes Inteligentes delimitados (DevOps, SRE, CLI Architect).

## 📜 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
