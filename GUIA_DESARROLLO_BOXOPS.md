# 📘 Guía de Desarrollo para Despliegues en BoxOps

Esta guía establece los lineamientos arquitectónicos y de configuración para que los equipos de desarrollo preparen sus proyectos (APIs, Frontends, Microservicios) para ser orquestados exitosamente por **BoxOps**.

BoxOps abstrae la complejidad de la infraestructura (Proxy SSL, Bases de Datos, Caché), por lo que los desarrolladores deben enfocarse únicamente en la lógica de contenedor de su aplicación.

---

## 1. Regla de Oro: Separación de Infraestructura y Aplicación

**⚠️ NUNCA incluyas servicios de infraestructura base (`postgres`, `mysql`, `redis`, `minio`) en el `docker-compose.yml` de Producción.**

El entorno BoxOps ya provee estos servicios de manera global y optimizada en la red de Docker (`boxops-network`). Incluirlos en el archivo de la aplicación consumirá RAM innecesaria en el servidor y romperá el aislamiento de recursos administrado por DevOps.

### ❌ Lo que NO debes hacer (Docker Compose Incorrecto)
```yaml
version: "3.8"
services:
  api:
    image: mi-registry/mi-api:latest
  
  # ❌ INCORRECTO: DevOps ya provee la base de datos global.
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: root
```

### ✅ Lo que SÍ debes hacer (Docker Compose Correcto)
Tu archivo `docker-compose.yml` de producción debe contener **únicamente** el código puro de tu aplicación o sus *workers* asíncronos. BoxOps se encargará de inyectar las redes y reglas de enrutamiento web dinámicamente.

```yaml
version: "3.8"
services:
  api:
    image: mi-registry/mi-api:latest
    restart: unless-stopped
    # El puerto interno EXPOSE es lo único relevante.
    # NO expongas puertos al host (NO uses `ports: - 8080:8080`).
    # Traefik se encargará de exponerlo seguramente al dominio público.
    
  worker:
    image: mi-registry/mi-api-worker:latest
    restart: unless-stopped
    # Este worker no necesita dominio publico, corre en el fondo.
```

---

## 2. Abstracción por Variables de Entorno (`.env`)

Conectar tu aplicación a la base de datos de producción es extremadamente fácil porque tu App y la Base de Datos Global viven en la **misma red interna de Docker** administrada por BoxOps.

El Administrador DevOps utilizará el asistente `boxops db wizard` para crearte una Base de Datos Lógica aislada y te entregará las credenciales a través de un archivo `.env`.

### Nombres de Host Internos de BoxOps
Para conectar tu aplicación a los servicios, en lugar de usar `localhost` o una IP pública, debes usar los nombres DNS internos del ecosistema BoxOps:

- **Base de Datos (PostgreSQL):** `boxops-postgres` (Puerto interno: `5432`)
- **Base de Datos (MySQL):** `boxops-mysql` (Puerto interno: `3306`)
- **Caché (Redis):** `boxops-redis` (Puerto interno: `6379`)
- **Object Storage (MinIO):** `boxops-minio` (Puerto interno API: `9000`)

### Ejemplo de Configuración (`.env`) en Producción
```env
# URL inyectada por DevOps (Se resuelve internamente a máxima velocidad)
DATABASE_URL="postgresql://api_user:super_password@boxops-postgres:5432/api_db"
REDIS_URL="redis://boxops-redis:6379/1"
MINIO_ENDPOINT="boxops-minio"
MINIO_PORT=9000
```
*Asegúrate de que tu código soporte la lectura dinámica de estas URIs.*

---

## 3. Manejo de Puertos e Interfaces (Traefik)

BoxOps utiliza **Traefik v3** como Reverse Proxy mágico. Cuando el Administrador despliegue tu aplicación, la CLI de BoxOps inspeccionará tu `docker-compose.yml` e inyectará los *labels* necesarios (`traefik.http.routers...`) en el servicio que actúe como "web/api".

Por esta razón, **está estrictamente prohibido** que mapees puertos al Host (`ports: - "3000:3000"`) en tu archivo Compose de producción.

1. Tu contenedor solo debe exponer su puerto internamente (vía Dockerfile `EXPOSE 3000` o simplemente escuchando en ese puerto en tu código Python/Node/Go).
2. Traefik enrutará el tráfico HTTP/HTTPS exterior directamente a la IP privada de tu contenedor hacia ese puerto interno.

---

## 4. Flujo de Trabajo y Entrega (Hand-off) a DevOps

1. Configura tu repositorio Git con tu `docker-compose.yml` limpio.
2. Asegúrate de incluir un archivo `.env.example` mencionando qué variables necesitan llenarse para que tu app sobreviva.
3. El administrador de BoxOps clonará tu repositorio.
4. BoxOps le pedirá al administrador:
   - *"¿A qué dominio público apuntará esta aplicación?"* -> `api.tuempresa.com`
   - *"¿Hacia qué puerto interno escucha tu contenedor web principal?"* -> `3000`
5. BoxOps sobrescribirá dinámicamente tu contenedor inyectando el SSL y levantará tu aplicación junto a tu propio archivo `.env` rellenado por DevOps.

¡Felicidades! Al cumplir estos lineamientos, tu aplicación garantiza tiempos de despliegue < 30 segundos, cero conflictos de puertos y una arquitectura en la nube escalable.
