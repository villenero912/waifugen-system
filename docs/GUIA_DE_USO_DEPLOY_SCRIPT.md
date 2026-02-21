# Guía de Uso: Script de Despliegue Automatizado de WaifuGen v2

Este documento proporciona instrucciones detalladas sobre cómo utilizar el script `deploy.sh` para automatizar la subida, configuración e instalación del sistema WaifuGen v2 en un servidor remoto.

## 1. Propósito del Script

El script `deploy.sh` está diseñado para simplificar el proceso de despliegue del sistema WaifuGen v2. Realiza las siguientes tareas:

*   **Verificación de Prerrequisitos:** Asegura que las herramientas necesarias (SSH, SCP) y el archivo ZIP del sistema corregido estén disponibles localmente.
*   **Recopilación de Detalles del Servidor:** Solicita al usuario el nombre de usuario SSH y la dirección IP/hostname del servidor remoto.
*   **Configuración de Variables de Entorno:** Permite al usuario introducir de forma segura las claves de API y otras variables de entorno críticas que se almacenarán en el archivo `.env` del servidor remoto.
*   **Subida del Archivo:** Copia el archivo `waifugen_v2_corrected.zip` al servidor remoto.
*   **Configuración Remota:** Se conecta al servidor remoto vía SSH y ejecuta una serie de comandos para:
    *   Crear el directorio del proyecto.
    *   Descomprimir el archivo del sistema.
    *   Crear el archivo `.env` con las variables proporcionadas.
    *   Instalar dependencias del sistema (como `ffmpeg`).
    *   Instalar dependencias de Python (`pip3`).
    *   Ejecutar las pruebas de verificación para asegurar que el sistema funciona correctamente.
    *   Limpiar el archivo ZIP temporal.

## 2. Prerrequisitos

Antes de ejecutar el script, asegúrate de cumplir con los siguientes requisitos:

*   **Acceso SSH:** Debes tener acceso SSH al servidor remoto. Esto implica tener tu clave SSH configurada para autenticación sin contraseña o estar preparado para introducir tu contraseña SSH cuando se te solicite.
*   **Archivo ZIP Corregido:** El archivo `waifugen_v2_corrected.zip` debe estar disponible en la ruta local especificada en el script (por defecto, `/home/ubuntu/waifugen_v2_corrected.zip`).
*   **Herramientas Locales:** Debes tener `ssh` y `scp` instalados en tu máquina local.
*   **Python 3 y Pip:** El servidor remoto debe tener Python 3 y `pip3` instalados.
*   **Sudo:** El usuario remoto debe tener permisos `sudo` para instalar paquetes del sistema (como `ffmpeg`).

## 3. Cómo Usar el Script `deploy.sh`

Sigue estos pasos para utilizar el script de despliegue:

### Paso 1: Hacer el Script Ejecutable

Primero, dale permisos de ejecución al script:

```bash
chmod +x deploy.sh
```

### Paso 2: Ejecutar el Script

Ejecuta el script desde tu terminal local:

```bash
./deploy.sh
```

### Paso 3: Proporcionar Información Solicitada

El script te guiará a través de las siguientes entradas:

1.  **Usuario SSH del servidor remoto:** Introduce el nombre de usuario que utilizas para conectarte a tu servidor (ej. `ubuntu`, `root`).
2.  **Dirección IP o Hostname del servidor remoto:** Introduce la dirección IP pública o el nombre de host de tu servidor.
3.  **ENCRYPTION_KEY:** Introduce la clave de encriptación que utilizará el sistema. **Esta clave es crítica para la seguridad y debe ser única y robusta.** No se mostrará en pantalla mientras la escribes.
4.  **Claves de API (Opcional):** Si utilizas servicios como OpenAI, Google o Telegram, se te pedirá que introduzcas sus respectivas claves de API y IDs de chat. Estas también se introducirán de forma segura.

### Paso 4: Monitorear el Despliegue

El script mostrará el progreso de la subida y la configuración remota. Presta atención a cualquier mensaje de error. Si todo va bien, verás un mensaje de éxito al final.

### Paso 5: Iniciar el Sistema en el Servidor Remoto

Una vez que el script haya finalizado, puedes conectarte a tu servidor remoto vía SSH y navegar al directorio del proyecto para iniciar la aplicación:

```bash
ssh usuario@ip_de_tu_servidor
cd /home/usuario/waifugen_v2  # Reemplaza 'usuario' con tu nombre de usuario
python3 main.py
```

## 4. Solución de Problemas Comunes

*   **"Error: El archivo ZIP corregido no se encuentra..."**: Asegúrate de que `waifugen_v2_corrected.zip` está en la ruta correcta o actualiza la variable `LOCAL_ZIP_FILE` en el script.
*   **"Error: SSH no está instalado..."**: Instala OpenSSH client en tu máquina local.
*   **Errores de permisos SSH:** Asegúrate de que tu clave SSH está configurada correctamente o que estás introduciendo la contraseña SSH correcta.
*   **Errores de instalación de dependencias:** Verifica la conexión a internet de tu servidor remoto y que el usuario tenga permisos `sudo`.
*   **`RuntimeError: ENCRYPTION_KEY no configurada en .env`**: Asegúrate de haber introducido la `ENCRYPTION_KEY` cuando el script te la solicitó. Si no, edita manualmente el archivo `.env` en el servidor remoto.

Este script está diseñado para ser un punto de partida. Para entornos de producción, se recomienda una solución de despliegue más robusta y segura.
