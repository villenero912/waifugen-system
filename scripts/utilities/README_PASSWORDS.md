# Generador de Contraseñas Seguras - WaifuGen System

## Descripción

Este conjunto de scripts genera contraseñas seguras y **deterministas** para todos los servicios del sistema WaifuGen usando una contraseña maestra.

### ¿Qué significa "determinista"?

Las contraseñas generadas son **siempre las mismas** cuando usas la misma contraseña maestra. Esto significa que:

✅ Puedes regenerar tus contraseñas en cualquier momento  
✅ No necesitas guardar las contraseñas individuales  
✅ Solo necesitas recordar la contraseña maestra: `Otoñoazul82@`  
✅ Las contraseñas son únicas para cada servicio  

## Archivos Incluidos

- **`generate_passwords.py`** - Script principal en Python
- **`generate_passwords.sh`** - Wrapper para Linux/Mac
- **`generate_passwords.ps1`** - Wrapper para Windows PowerShell

## Uso

### Opción 1: Windows (PowerShell)

```powershell
# Generar archivo .env con contraseñas
cd "C:\Users\Sebas\Downloads\package (1)\waifugen_system"
.\scripts\utilities\generate_passwords.ps1

# Con contraseña maestra personalizada
.\scripts\utilities\generate_passwords.ps1 -MasterPassword "MiContraseña" -OutputFile ".env"
```

### Opción 2: Linux/Mac (Bash)

```bash
# Generar archivo .env con contraseñas
cd ~/waifugen_system
chmod +x scripts/utilities/generate_passwords.sh
./scripts/utilities/generate_passwords.sh

# Con contraseña maestra personalizada
./scripts/utilities/generate_passwords.sh "MiContraseña" ".env"
```

### Opción 3: Python Directamente

```bash
# Generar y mostrar en pantalla
python scripts/utilities/generate_passwords.py

# Generar y guardar en archivo
python scripts/utilities/generate_passwords.py --output .env

# Con contraseña maestra personalizada
python scripts/utilities/generate_passwords.py --master "MiContraseña" --output .env

# Mostrar en formato tabla
python scripts/utilities/generate_passwords.py --format table

# Verificar determinismo
python scripts/utilities/generate_passwords.py --verify
```

## Contraseñas Generadas

El script genera las siguientes contraseñas:

| Variable | Servicio | Longitud |
|----------|----------|----------|
| `POSTGRES_PASSWORD` | Base de datos PostgreSQL | 40 caracteres |
| `REDIS_PASSWORD` | Cache Redis | 40 caracteres |
| `SECRET_KEY` | Aplicación Flask/Django | 64 caracteres |
| `GRAFANA_PASSWORD` | Panel Grafana | 40 caracteres |
| `JWT_SECRET` | Tokens JWT | 64 caracteres |
| `ENCRYPTION_KEY` | Encriptación de datos | 64 caracteres |

## Seguridad

### Algoritmo Utilizado

- **PBKDF2-HMAC-SHA256** - Estándar de la industria
- **100,000 iteraciones** - Protección contra ataques de fuerza bruta
- **Salt único por servicio** - Cada contraseña es única
- **Base64 URL-safe** - Compatible con todas las aplicaciones

### Contraseña Maestra

La contraseña maestra por defecto es: **`Otoñoazul82@`**

Esta contraseña:
- ✅ Tiene 12 caracteres
- ✅ Incluye mayúsculas y minúsculas
- ✅ Incluye números
- ✅ Incluye caracteres especiales
- ✅ Es fácil de recordar para ti

### Mejores Prácticas

1. **Guarda la contraseña maestra de forma segura**
   - Usa un gestor de contraseñas (1Password, Bitwarden, etc.)
   - Escríbela en papel y guárdala en un lugar seguro
   - No la compartas con nadie

2. **Rota las contraseñas cada 90 días**
   ```bash
   # Cambiar la contraseña maestra
   python generate_passwords.py --master "NuevaContraseña2026" --output .env
   ```

3. **Nunca subas el archivo .env a Git**
   - Ya está incluido en `.gitignore`
   - Verifica antes de hacer commit

4. **Establece permisos seguros**
   ```bash
   chmod 600 .env
   ```

## Regeneración de Contraseñas

Si pierdes el archivo `.env`, puedes regenerarlo usando la misma contraseña maestra:

```bash
# Las contraseñas serán EXACTAMENTE las mismas
python scripts/utilities/generate_passwords.py --master "Otoñoazul82@" --output .env
```

## Verificación

Para verificar que las contraseñas son deterministas:

```bash
python scripts/utilities/generate_passwords.py --verify
```

Esto generará las contraseñas dos veces y verificará que sean idénticas.

## Ejemplo de Salida

```env
# ============================================================================
# CONTRASEÑAS GENERADAS - Sistema WaifuGen
# ============================================================================

POSTGRES_PASSWORD=8KxN_vYmZ3pQrT2wL9jH5fD1cB6nM4sA7eG0iU
REDIS_PASSWORD=3FhJ8kL2mP5qR9tV1wX4yZ7aC0dE6gI9jK2nO
SECRET_KEY=5BcD8eF1gH4jK7mN0pQ3rS6tU9vW2xY5zA8bC1dE4fG7hI0jK3lM6nO9pQ2rS5tU8vW
GRAFANA_PASSWORD=7DfG0hI3jK6lM9nO2pQ5rS8tU1vW4xY7zA0bC
JWT_SECRET=9EgH2iJ5kL8mN1oP4qR7sT0uV3wX6yZ9aB2cD5eF8gH1iJ4kL7mN0oP3qR6sT9uV2wX
ENCRYPTION_KEY=1FhI4jK7lM0nO3pQ6rS9tU2vW5xY8zA1bC4dE7fG0hI3jK6lM9nO2pQ5rS8tU1vW4xY
```

## Solución de Problemas

### Error: Python no encontrado

**Windows:**
```powershell
# Instalar Python desde Microsoft Store
winget install Python.Python.3.11
```

**Linux:**
```bash
sudo apt update
sudo apt install python3
```

### Error: Permisos denegados

**Linux/Mac:**
```bash
chmod +x scripts/utilities/generate_passwords.sh
```

**Windows:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Integración con Deploy

Después de generar las contraseñas, puedes desplegar directamente:

```bash
# Generar contraseñas
python scripts/utilities/generate_passwords.py --output .env

# Editar y añadir claves API
nano .env

# Desplegar al VPS
./scripts/deploy_env.sh
```

## Preguntas Frecuentes

**P: ¿Puedo cambiar la contraseña maestra?**  
R: Sí, pero recuerda que esto generará contraseñas completamente diferentes. Si ya tienes el sistema en producción, tendrás que actualizar todos los servicios.

**P: ¿Las contraseñas son seguras?**  
R: Sí, utilizan PBKDF2-HMAC-SHA256 con 100,000 iteraciones, que es el estándar recomendado por NIST y OWASP.

**P: ¿Qué pasa si olvido la contraseña maestra?**  
R: Tendrás que generar nuevas contraseñas con una nueva contraseña maestra y actualizar todos los servicios. Por eso es importante guardarla de forma segura.

**P: ¿Puedo usar este script para otros proyectos?**  
R: Sí, solo cambia el salt en el código (línea que dice `waifugen_system`) por el nombre de tu proyecto.

## Soporte

Si tienes problemas con el generador de contraseñas, verifica:

1. ✅ Python 3.6+ está instalado
2. ✅ Tienes permisos de escritura en el directorio
3. ✅ La contraseña maestra no contiene caracteres especiales que puedan causar problemas en la terminal

---

**Última actualización:** 2026-01-31  
**Versión:** 1.0.0  
**Autor:** Sistema WaifuGen
