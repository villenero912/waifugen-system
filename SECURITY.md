# Guía de Seguridad - WaifuGen System

Este documento resume las medidas de seguridad implementadas y los pasos necesarios para mantener el sistema protegido.

## 🛡️ Medidas de Seguridad Implementadas

1.  **Hardening del Servidor**:
    *   Configuración automática de Firewall (UFW) permitiendo solo puertos esenciales (22, 80, 443).
    *   Protección contra fuerza bruta mediante **Fail2Ban**.
    *   Desactivación de login SSH como `root`.
    *   Reducción de intentos de autenticación.

2.  **Seguridad de Aplicación**:
    *   **Dockerización**: Aislamiento de servicios.
    *   **Puertos Seguros**: PostgreSQL y Redis no están expuestos a Internet (binded a `127.0.0.1`).
    *   **Filtros de Contenido**: Protección contra Inyección SQL, XSS y Prompt Injection.
    *   **Auditoría de Secretos**: Se ha verificado que no existan claves API hardcodeadas en el código.

3.  **Privacidad de Datos**:
    *   `.gitignore` configurado para evitar la subida de archivos `.env`, bases de datos y archivos de cuentas personales.

## 🚀 Cómo aplicar el Hardening en tu VPS

Una vez que hayas subido el código a tu VPS, ejecuta el siguiente script con permisos de sudo:

```bash
chmod +x scripts/harden_server.sh
sudo ./scripts/harden_server.sh
```

**IMPORTANTE**: Asegúrate de tener acceso vía SSH antes de habilitar el firewall. Los puertos abiertos por defecto son 22 (SSH), 80 (HTTP) y 443 (HTTPS).

## 🔑 Gestión de Credenciales

*   Todas las claves API y contrasenas deben ir EXCLUSIVAMENTE en el archivo `.env`.
*   Nunca compartas el archivo `.env` ni lo subas a repositorios públicos.
*   Usa contraseñas fuertes generadas automáticamente por el script de despliegue.

## 📊 Monitoreo de Seguridad

Puedes monitorear intentos de intrusión y uso de recursos a través de:
*   **Grafana**: Acceso vía `http://tu-ip/grafana` (protegido por contraseña).
*   **Logs**: Ubicados en `data/logs/` y accesibles vía `docker compose logs`.
