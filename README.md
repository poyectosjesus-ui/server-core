# 📦 BoxOps CLI (PaaS Edition)

![Version](https://img.shields.io/badge/version-2.0.0--beta-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Deployments](https://img.shields.io/badge/deployments-Traefik--S3-orange.svg)

**BoxOps** ha evolucionado de un simple script bash a una **Plataforma como Servicio (PaaS) privada y CLI de grado Enterprise**. Su objetivo es permitir a administradores DevOps y desarrolladores orquestar infraestructura compleja y publicar aplicaciones (Workloads) en segundos con Arquitectura Cliente-Servidor (Zero-Downtime y SSL Dinámico).

## 🚀 La Magia del Cliente-Servidor

BoxOps funciona tanto en el **Servidor (Infraestructura)** como en la **Máquina Local del DevOps (Cliente)**:

1. **En tu Servidor:** Construye clústeres de Traefik, Prometheus, Grafana, MinIO (S3), Redis y PostgreSQL usando asistentes interactivos en Python.
2. **En tu Laptop:** Abres cualquier proyecto (API, Frontend, Node, Python, etc.), escribes `boxops push` y el código vuela vía SSH, inyectándose automáticamente en el proxy de tu servidor con un certificado Let's Encrypt vigente.

## 🛠️ Instalación Rápida

### 1. En el Servidor (Host)
Inicia sesión vía SSH en tu servidor Debian/Ubuntu y ejecuta:
```bash
git clone https://github.com/tu-usuario/server-core.git
cd server-core
chmod +x install.sh
sudo ./install.sh
```
Usa el **Asistente (Opción 1)** para aprovisionar el servidor e instalar toda la infraestructura global en Docker.

### 2. En tu Máquina Local (MacOS / Windows / Linux)
Clona este mismo repositorio en tu computadora de uso diario, y usa Python para instalar la CLI globalmente:
```bash
git clone https://github.com/tu-usuario/server-core.git
cd server-core
pip install -e .
```
Conecta tu CLI local al servidor que acabas de instalar:
```bash
boxops remote add IP_DE_TU_SERVIDOR
```

## 🏗️ Guía de Uso
Para ver el flujo de trabajo completo, creación de bases de datos aisladas e interacción remota, por favor dirígete a:
- 📖 [MANUAL_CLI.md](./MANUAL_CLI.md) (Todos los comandos explicados)
- 👨‍💻 [GUIA_DESARROLLO_BOXOPS.md](./GUIA_DESARROLLO_BOXOPS.md) (Reglas de Arquitectura para el equipo dev)

## 📜 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
