# 📖 BoxOps - Manual Completo de la CLI

BoxOps es una CLI interactiva basada en Python (`Typer` y `Questionary`). Está diseñada con el flujo de trabajo de SysAdmins en mente. 

A continuación se listan todos los submódulos y comandos disponibles.

---

## 🏗️ 1. Infraestructura Base (`boxops infra`)
*Comandos diseñados para ejecutarse exclusivamente en el **Servidor Remoto**.*

- `sudo boxops infra wizard`: El comando estrella. Es un asistente de UI interactiva (multi-selección) que despliega infraestructura de forma idempotente de la siguiente lista:
  - Reverse Proxy (Traefik v3)
  - Capa de Observabilidad (Prometheus + Grafana)
  - Base de Datos SQL Global (PostgreSQL)
  - Caché Local Global (Redis)
  - Almacenamiento S3 Avanzado (MinIO)
  - Respaldos Automatizados Diarios de DB (pg-backups)
  
- `sudo boxops infra down`: Comando para destruir componentes globales específicos.

---

## 🗄️ 2. Bases de Datos (`boxops db`)
*Ideal para gestionar accesos seguros de aplicaciones sin escribir SQL.*

- `sudo boxops db wizard`: Ejecuta el DBA Asistente. Te guiará paso a paso para:
  - Crear un usuario PostgreSQL seguro (con contraseña compleja auto-generada).
  - Crear una Base de Datos Lógica aislada.
  - Atar ese usuario exclusivamente a esa BD.
  - Generarte el `Connection String` de salida (*ej. postgres://user:pass@host/db*) listo para que se lo entregues a tus desarrolladores en un `.env`.

- `sudo boxops db create-instance`: Levanta un motor de BD en un contenedor totalmente dedicado si necesitas que un cliente no comparta recursos globales.

---

## 🚀 3. Flujo Local del DevOps (`boxops remote` y `boxops push`)
*Comandos diseñados para ejecutarse exclusivamente en **Tu Laptop (Local)**.*

- `boxops remote add [IP]`: Configura la diana de despliegue. Guarda en `~/.boxops/config.json` la IP remota protegida por tu llave SSH.
- `boxops remote status`: Muestra a qué servidor apuntan tus despliegues actuales.

- `boxops push`: 
  1. Se ejecuta estando dentro de la carpeta de cualquier proyecto de software web.
  2. Sincroniza todos tus archivos (excepto `.git` y `node_modules`) al servidor remoto en 1 segundo usando `rsync`.
  3. Ejecuta el parseador YAML remoto. Te pregunta interactivamente en qué dominio publicarás el proyecto y qué servicio quieres exponer a Internet.
  4. Levanta el proyecto modificado detrás de Traefik.

---

## 📦 4. Gestión de Aplicaciones en Servidor (`boxops app`)

- `sudo boxops app list`: Imprime una tabla estructurada listando todas las aplicaciones (Workloads) que están corriendo en ese servidor junto con el estado del contenedor Docker.
- `sudo boxops app remove`: Abre una lista interactiva de las apps actualmente activas. Permite dar de baja un proyecto de forma segura, desmontando su Docker Compose y eliminando su carpeta maestra del servidor para liberar espacio.

---

## 🔧 Archivos Clave del Sistema
- **Carpeta de Infraestructura:** `/opt/boxops/infra` (Traefik, Prometheus, DBs globales)
- **Carpeta de Aplicaciones:** `/opt/boxops/apps/` (Cada Sub-carpeta es un Workload)
- **Red Aislada Transversal:** `boxops-network` (Todos los contenedores deben atarse aquí para ver la Base de Datos Global y Traefik).
