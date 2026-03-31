# Changelog

Todos los cambios notables en BoxOps serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere rigurosamente al versionado semántico: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-31
### Added
- **ChatOps Telegram Daemon (Phase 9)**: Process de long-polling seguro que escucha `/help`, `/status`, `/apps` y `/backup` reportando vía Telegram directo al SysAdmin. Soporta reconfiguración nativa mediante `boxops daemon config`.
- **Global Status Dashboard (`boxops status`)**: Dashboard de hardware que reporta uso porcentual de RAM y CPU de todos los contenedores de BoxOps, validando existencia física del último Volcado de Datos.
- **Client-Server Remote Protocol (`boxops push`)**: Ejecución Local-Remoto permitiendo empujar Workloads desde la Macbook del desarrollador al Servidor en Ubuntu.
- **Dynamic Infrastructure Catalog (`boxops infra wizard`)**: El código duro mutó en un motor de inyección de Docker-Composes a demanda (Proxy, MinIO, Redis, Postgres).

## [0.1.0-mvp] - 2026-03-31
### Added
- Documentación semilla del proyecto (`README.md`, `LICENSE`, `CHANGELOG.md`).
- Documentos de planeación de producto en la subcarpeta del cerebro IA (`implementation_plan.md`, `mvp.md`, `ai_agents.md`).
- `install.sh` inicial para bootstrapper de sistemas operativos Debian/Ubuntu.
- Andamiaje base de la CLI desarrollada en Python aprovechando las potencias gráficas de `TYPER` y `RICH`.
