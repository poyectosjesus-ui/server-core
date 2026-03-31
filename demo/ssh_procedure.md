# Procedimiento de Pruebas SSH (BoxOps Demo)

Este documento detalla los pasos que el Asistente de IA ejecutará de forma autónoma para conectarse al servidor Demo, realizar el despliegue y verificar que el entorno funcione de manera óptima usando los datos definidos en `.env`.

## Fase 1: Lectura de Credenciales
El asistente extraerá las variables del archivo `demo/.env` local para formular el comando SSH.
* Variables esperadas: `DEMO_SERVER_HOST`, `DEMO_SERVER_PORT`, `DEMO_SERVER_USER`, y la ruta de la llave (`DEMO_SSH_KEY_PATH`) o contraseña.

## Fase 2: Comprobación de Conectividad (Ping SSH)
Antes de enviar comandos pesados, se realizará una prueba de conexión rápida y sin interacción para asegurar la integridad del acceso:
```bash
ssh -i $DEMO_SSH_KEY_PATH -p $DEMO_SERVER_PORT -o StrictHostKeyChecking=no -o BatchMode=yes $DEMO_SERVER_USER@$DEMO_SERVER_HOST "echo 'Conexión Exitosa'"
```
*Si falla, el asistente analizará el error (ej. Timeout, llave denegada) y se lo reportará al usuario.*

## Fase 3: Transferencia del Instalador
A través de `scp` o `rsync`, el asistente enviará la carpeta del proyecto actual (`server-core`) al directorio del usuario remoto (ej. `/tmp/boxops-demo`).
```bash
scp -i $DEMO_SSH_KEY_PATH -P $DEMO_SERVER_PORT -r ../server-core $DEMO_SERVER_USER@$DEMO_SERVER_HOST:/tmp/boxops-demo
```

## Fase 4: Despliegue (Ejecución de install.sh)
El asistente se conectará mediante SSH para dar permisos de ejecución y correr el instalador de forma no-interactiva o simulando las entradas (si el instalador aún requiere la pulsación de ENTER). Dado que el instalador interactivo es para humanos, para las pruebas se puede inyectar un input `echo 1 | ./install.sh`.

```bash
ssh -i $DEMO_SSH_KEY_PATH -p $DEMO_SERVER_PORT $DEMO_SERVER_USER@$DEMO_SERVER_HOST "cd /tmp/boxops-demo && chmod +x install.sh && echo 1 | sudo ./install.sh"
```

## Fase 5: Verificaciones Post-Instalación
El asistente correrá una serie de comandos de diagnóstico remotos para validar el éxito de BoxOps:
1. **Verificar directorio base**: `ls -la /opt/boxops`
2. **Verificar entorno Python**: `/opt/boxops/venv/bin/python --version`
3. **Verificar symlink de BoxOps**: `boxops --help`
4. **Verificar dependencias de Infraestructura**: `docker ps` y `ufw status`

## Fase 6: Cierre y Limpieza
Tras validar cada comando, el asistente presentará un reporte en el chat informando qué módulos se instalaron con éxito y si ocurrió alguna divergencia en los logs remotos. Opcionalmente ejecutará la opción 3 (Desinstalar) para restaurar el servidor demo a su estado original si el usuario lo demanda.
