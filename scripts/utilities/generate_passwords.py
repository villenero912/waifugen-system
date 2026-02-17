#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
Generador de Contraseñas Seguras - Sistema WaifuGen
============================================================================
Este script genera contraseñas seguras y deterministas usando una contraseña
maestra. Las contraseñas generadas son siempre las mismas para la misma
contraseña maestra, lo que permite regenerarlas cuando sea necesario.

Uso:
    python generate_passwords.py
    python generate_passwords.py --master "TuContraseñaMaestra"
    python generate_passwords.py --output .env

Características:
- Derivación determinista usando PBKDF2-HMAC-SHA256
- Contraseñas únicas para cada servicio
- Formato base64 seguro para URLs
- Longitud configurable (por defecto 32 caracteres)
============================================================================
"""

import hashlib
import base64
import argparse
import sys
from typing import Dict


class PasswordGenerator:
    """Generador de contraseñas deterministas usando PBKDF2."""
    
    def __init__(self, master_password: str):
        """
        Inicializa el generador con una contraseña maestra.
        
        Args:
            master_password: Contraseña maestra para derivar todas las demás
        """
        self.master_password = master_password.encode('utf-8')
    
    def generate(self, service_name: str, length: int = 32, iterations: int = 100000) -> str:
        """
        Genera una contraseña segura para un servicio específico.
        
        Args:
            service_name: Nombre del servicio (ej: "postgres", "redis")
            length: Longitud deseada de la contraseña (por defecto 32)
            iterations: Número de iteraciones PBKDF2 (por defecto 100000)
        
        Returns:
            Contraseña segura en formato base64
        """
        # Usar el nombre del servicio como salt
        salt = f"waifugen_system_{service_name}_2026".encode('utf-8')
        
        # Derivar clave usando PBKDF2-HMAC-SHA256
        derived_key = hashlib.pbkdf2_hmac(
            'sha256',
            self.master_password,
            salt,
            iterations,
            dklen=length
        )
        
        # Convertir a base64 URL-safe y truncar a la longitud deseada
        password = base64.urlsafe_b64encode(derived_key).decode('utf-8')
        
        # Remover caracteres de padding y truncar
        password = password.replace('=', '').replace('-', '_')[:length]
        
        return password
    
    def generate_all(self) -> Dict[str, str]:
        """
        Genera todas las contraseñas necesarias para el sistema WaifuGen.
        
        Returns:
            Diccionario con todas las contraseñas generadas
        """
        return {
            'POSTGRES_PASSWORD': self.generate('postgres', 40),
            'REDIS_PASSWORD': self.generate('redis', 40),
            'SECRET_KEY': self.generate('secret_key', 64),
            'GRAFANA_PASSWORD': self.generate('grafana', 40),
            'JWT_SECRET': self.generate('jwt_secret', 64),
            'ENCRYPTION_KEY': self.generate('encryption', 64),
        }


def print_passwords(passwords: Dict[str, str], format_type: str = 'env'):
    """
    Imprime las contraseñas en el formato especificado.
    
    Args:
        passwords: Diccionario de contraseñas
        format_type: Formato de salida ('env', 'json', 'table')
    """
    if format_type == 'env':
        print("# ============================================================================")
        print("# CONTRASEÑAS GENERADAS - Sistema WaifuGen")
        print("# ============================================================================")
        print("# ADVERTENCIA: Estas contraseñas son sensibles. Guárdalas de forma segura.")
        print("# Generadas usando derivación PBKDF2-HMAC-SHA256")
        print("# ============================================================================")
        print()
        for key, value in passwords.items():
            print(f"{key}={value}")
        print()
        print("# ============================================================================")
        print("# IMPORTANTE: Copia estas contraseñas a tu archivo .env")
        print("# ============================================================================")
    
    elif format_type == 'json':
        import json
        print(json.dumps(passwords, indent=2))
    
    elif format_type == 'table':
        print("\n" + "="*80)
        print(f"{'SERVICIO':<25} {'CONTRASEÑA':<55}")
        print("="*80)
        for key, value in passwords.items():
            # Mostrar solo los primeros y últimos caracteres por seguridad
            masked = f"{value[:8]}...{value[-8:]}" if len(value) > 20 else value
            print(f"{key:<25} {masked:<55}")
        print("="*80)
        print("\n⚠️  Las contraseñas completas se han generado correctamente.")
        print("   Usa --format env para ver las contraseñas completas.\n")


def create_env_file(passwords: Dict[str, str], master_password: str, output_file: str = '.env'):
    """
    Crea un archivo .env completo con todas las variables de entorno.
    
    Args:
        passwords: Diccionario de contraseñas generadas
        master_password: Contraseña maestra (para mostrar en comentarios)
        output_file: Ruta del archivo de salida
    """
    env_content = f"""# ============================================================================
# SISTEMA WAIFUGEN - VARIABLES DE ENTORNO
# ============================================================================
# ADVERTENCIA DE SEGURIDAD: Este archivo contiene credenciales sensibles
# Permisos recomendados: chmod 600 .env
# NUNCA subir este archivo a Git
# ============================================================================
# Contraseñas generadas automáticamente usando contraseña maestra
# Contraseña maestra: {master_password}
# Fecha de generación: {get_current_date()}
# ============================================================================

# ============================================================================
# CONFIGURACIÓN DEL PROYECTO
# ============================================================================
PROJECT_NAME=waifugen_system
TIMEZONE=Europe/Madrid
DEBUG=false
LOG_LEVEL=INFO

# ============================================================================
# CREDENCIALES DE BASE DE DATOS
# ============================================================================
POSTGRES_DB=waifugen_production
POSTGRES_USER=waifugen_user
POSTGRES_PASSWORD={passwords['POSTGRES_PASSWORD']}
POSTGRES_PORT=5432

# ============================================================================
# CREDENCIALES DE REDIS CACHE
# ============================================================================
REDIS_PASSWORD={passwords['REDIS_PASSWORD']}
REDIS_PORT=6379

# ============================================================================
# CLAVE SECRETA DE LA APLICACIÓN
# ============================================================================
# Usada para tokens JWT, firma de sesiones, encriptación
SECRET_KEY={passwords['SECRET_KEY']}

# ============================================================================
# CLAVES ADICIONALES DE SEGURIDAD
# ============================================================================
JWT_SECRET={passwords['JWT_SECRET']}
ENCRYPTION_KEY={passwords['ENCRYPTION_KEY']}

# ============================================================================
# CONFIGURACIÓN DE A2E API (REQUERIDO - Fase 1)
# ============================================================================
# Obtén tu clave API desde: https://www.a2e.ai/account/api
A2E_API_KEY=sk_YOUR_A2E_API_KEY_HERE

# ============================================================================
# REPLICATE API (OPCIONAL - Para Generación de Música)
# ============================================================================
REPLICATE_API_TOKEN=r8_YOUR_REPLICATE_TOKEN_HERE

# ============================================================================
# PIXABAY API (OPCIONAL - Para Biblioteca de Música)
# ============================================================================
PIXABAY_API_KEY=YOUR_PIXABAY_API_KEY_HERE

# ============================================================================
# NOTIFICACIONES DE TELEGRAM (OPCIONAL - Recomendado)
# ============================================================================
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_FROM_BOTFATHER
TELEGRAM_ADMIN_CHAT_ID=YOUR_CHAT_ID_NUMBER

# ============================================================================
# CONFIGURACIÓN DE OLLAMA LLM
# ============================================================================
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_PORT=11434

# ============================================================================
# MONITOREO CON GRAFANA (OPCIONAL)
# ============================================================================
GRAFANA_USER=admin
GRAFANA_PASSWORD={passwords['GRAFANA_PASSWORD']}

# ============================================================================
# PUERTO DE LA APLICACIÓN
# ============================================================================
APP_PORT=8000

# ============================================================================
# N8N WORKFLOW AUTOMATION
# ============================================================================
WEBHOOK_URL=

# ============================================================================
# FASE 2 - SERVICIOS AVANZADOS (Configurar cuando sea necesario)
# ============================================================================
# RUNPOD_API_KEY=YOUR_RUNPOD_API_KEY_WHEN_READY
# MODAL_API_KEY=YOUR_MODAL_API_KEY_WHEN_READY
# ONLYFANS_API_KEY=YOUR_OF_API_KEY_WHEN_READY
# ONLYFANS_USER_ID=YOUR_OF_USER_ID

# ============================================================================
# INFORMACIÓN DE ROTACIÓN
# ============================================================================
# Última generación: {get_current_date()}
# Próxima rotación: {get_next_rotation_date()}
# Para regenerar: python scripts/utilities/generate_passwords.py --master "{master_password}"
# ============================================================================
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"\n✅ Archivo {output_file} creado exitosamente")
    print(f"📝 Recuerda añadir tus claves API (A2E, Telegram, etc.)")
    print(f"🔒 Establece permisos seguros: chmod 600 {output_file}")


def get_current_date() -> str:
    """Obtiene la fecha actual en formato ISO."""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d')


def get_next_rotation_date() -> str:
    """Calcula la fecha de próxima rotación (+90 días)."""
    from datetime import datetime, timedelta
    next_rotation = datetime.now() + timedelta(days=90)
    return next_rotation.strftime('%Y-%m-%d')


def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Generador de contraseñas seguras para WaifuGen System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  # Generar contraseñas con la contraseña maestra por defecto
  python generate_passwords.py
  
  # Usar una contraseña maestra personalizada
  python generate_passwords.py --master "MiContraseñaSegura123"
  
  # Generar y guardar en archivo .env
  python generate_passwords.py --output .env
  
  # Mostrar en formato tabla
  python generate_passwords.py --format table
        """
    )
    
    parser.add_argument(
        '--master',
        type=str,
        default='Otoñoazul82@',
        help='Contraseña maestra para derivar todas las demás (por defecto: Otoñoazul82@)'
    )
    
    parser.add_argument(
        '--format',
        type=str,
        choices=['env', 'json', 'table'],
        default='env',
        help='Formato de salida (por defecto: env)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Guardar en archivo (ej: .env)'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verificar que las contraseñas son deterministas'
    )
    
    args = parser.parse_args()
    
    # Generar contraseñas
    generator = PasswordGenerator(args.master)
    passwords = generator.generate_all()
    
    # Verificar determinismo si se solicita
    if args.verify:
        print("🔍 Verificando determinismo de contraseñas...")
        generator2 = PasswordGenerator(args.master)
        passwords2 = generator2.generate_all()
        
        if passwords == passwords2:
            print("✅ Verificación exitosa: Las contraseñas son deterministas")
        else:
            print("❌ Error: Las contraseñas no son deterministas")
            sys.exit(1)
    
    # Guardar en archivo si se especifica
    if args.output:
        create_env_file(passwords, args.master, args.output)
    else:
        # Imprimir en el formato especificado
        print_passwords(passwords, args.format)
    
    # Mostrar información de seguridad
    if not args.output:
        print("\n" + "="*80)
        print("📋 INFORMACIÓN DE SEGURIDAD")
        print("="*80)
        print(f"✓ Contraseña maestra: {args.master}")
        print(f"✓ Algoritmo: PBKDF2-HMAC-SHA256")
        print(f"✓ Iteraciones: 100,000")
        print(f"✓ Contraseñas generadas: {len(passwords)}")
        print("\n⚠️  IMPORTANTE:")
        print("   - Guarda la contraseña maestra en un lugar seguro")
        print("   - Puedes regenerar estas contraseñas usando la misma contraseña maestra")
        print("   - Nunca compartas las contraseñas generadas")
        print("="*80 + "\n")


if __name__ == '__main__':
    main()
