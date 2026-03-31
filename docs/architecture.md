# Arquitectura de Alto Rendimiento con Docker (BoxOps)

A continuación se muestra el diagrama de la arquitectura del servidor productivo abstracto propuesto para BoxOps. Representa el flujo de la infraestructura y no aplicaciones específicas.

```mermaid
graph TD
    classDef external fill:#2c3e50,stroke:#34495e,stroke-width:2px,color:#fff;
    classDef security fill:#e74c3c,stroke:#c0392b,stroke-width:2px,color:#fff;
    classDef proxy fill:#f39c12,stroke:#d35400,stroke-width:2px,color:#fff;
    classDef workload fill:#3498db,stroke:#2980b9,stroke-width:2px,color:#fff;
    classDef database fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff;
    classDef observability fill:#8e44ad,stroke:#9b59b6,stroke-width:2px,color:#fff;
    classDef tool fill:#95a5a6,stroke:#7f8c8d,stroke-width:2px,color:#fff;

    Internet((Internet)):::external
    DNS[DNS / WAF (e.g. Cloudflare)]:::external

    subgraph "Host Productivo (Docker Node)"
        BoxOps(BoxOps CLI\nMotor de Provisión CLI):::tool
        UFW[Firewall Host\nUFW + Fail2ban]:::security
        
        subgraph "Docker Engine Environment"
            Traefik[Reverse Proxy (Traefik/Nginx)\nRouter Global & SSL Automático]:::proxy
            
            subgraph "Stack de Observabilidad"
                Metrics[Prometheus\nColección de Métricas]:::observability
                Dashboards[Grafana\nVisualización y Alertas]:::observability
                Metrics --> Dashboards
            end

            subgraph "Carga de Trabajo (Workloads)"
                Apps[Contenedores de Aplicaciones\nMicroservicios / APIs / Frontends]:::workload
            end

            subgraph "Capa de Datos Global"
                SQL[(Bases de Datos Relacionales\nPostgreSQL / MySQL)]:::database
                NoSQL[(Caché / NoSQL\nRedis / MongoDB)]:::database
            end
            
            %% Flujos internos dentro del nodo Docker
            Apps --> SQL
            Apps --> NoSQL
        end
    end

    %% Flujos de Red Externos
    Internet --> DNS
    DNS --> UFW
    UFW --> Traefik
    
    %% Enrutamiento Interno
    Traefik ==>|Tráfico Web Dinámico| Apps
    Traefik -.->|Panel Administrativo| Dashboards
    
    %% Gestión y Orquestación
    BoxOps -.->|Despliega y Configura| Traefik
    BoxOps -.->|Provisiona Base de Datos| SQL
    BoxOps -.->|Orquesta Contenedores| Apps
    BoxOps -.->|Configura Monitoreo| Metrics
```
