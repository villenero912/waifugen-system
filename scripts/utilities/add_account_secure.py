#!/usr/bin/env python3
"""
Script de Ingesta Segura para WaifuGen
Permite cargar cuentas de redes sociales y proxies con encriptación AES-256.
"""

import os
import sys
import psycopg2
from getpass import getpass

# Importar el módulo de seguridad
sys.path.insert(0, '/root/waifugen-system')
from src.utils.security import vault

def connect_db():
    """Conecta a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            database=os.getenv('POSTGRES_DB', 'waifugen_prod'),
            user=os.getenv('POSTGRES_USER', 'waifugen_user'),
            password=os.getenv('POSTGRES_PASSWORD', 'WaifuGen2026Secure'),
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)

def add_account():
    """Añade una cuenta de red social con encriptación"""
    print("\n🔐 === AÑADIR CUENTA DE RED SOCIAL (SEGURO) ===\n")
    
    # Listar personajes disponibles
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM characters ORDER BY id")
    characters = cur.fetchall()
    
    print("Personajes disponibles:")
    for char_id, name in characters:
        print(f"  {char_id}. {name}")
    
    # Solicitar datos
    character_id = int(input("\nID del personaje: "))
    
    print("\nPlataformas disponibles (Phase 1):")
    print("  1. YouTube (Shorts)")
    print("  2. TikTok")
    print("  3. Instagram (Reels)")
    print("  4. Facebook (Reels)")
    print("  5. Discord")
    print("  6. LINE (Japan)")
    print("  7. Fantia (Japan)")
    print("  8. FC2 (Japan)")
    print("  9. Telegram")
    
    platform_choice = input("\nElige plataforma (1-9): ").strip()
    platform_map = {
        "1": "youtube",
        "2": "tiktok",
        "3": "instagram",
        "4": "facebook",
        "5": "discord",
        "6": "line",
        "7": "fantia",
        "8": "fc2",
        "9": "telegram"
    }
    
    platform = platform_map.get(platform_choice, "tiktok")
    username = input("Usuario/Email de la cuenta: ")
    password = getpass("Contraseña (no se mostrará): ")
    
    # Encriptar la contraseña
    password_encrypted = vault.encrypt(password)
    
    # Insertar en la base de datos
    cur.execute("""
        INSERT INTO accounts (character_id, platform, username, password_enc, status, region)
        VALUES (%s, %s, %s, %s, 'active', 'ES')
        RETURNING id
    """, (character_id, platform, username, password_encrypted))
    
    account_id = cur.fetchone()[0]
    conn.commit()
    
    print(f"\n✅ Cuenta añadida con éxito (ID: {account_id})")
    print(f"   Contraseña encriptada: {password_encrypted[:50]}...")
    
    cur.close()
    conn.close()

def add_proxy():
    """Añade un proxy con encriptación"""
    print("\n🔐 === AÑADIR PROXY (SEGURO) ===\n")
    
    proxy_type = input("Tipo de proxy (residential/datacenter/mobile): ").lower()
    host = input("Host del proxy (ej: proxy.iproyal.com): ")
    port = input("Puerto: ")
    username = input("Usuario del proxy: ")
    password = getpass("Contraseña del proxy (no se mostrará): ")
    
    # Encriptar la contraseña
    password_encrypted = vault.encrypt(password)
    
    # Insertar en la base de datos
    conn = connect_db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO proxies (proxy_type, host, port, username, password_enc, status, region)
        VALUES (%s, %s, %s, %s, %s, 'active', 'ES')
        RETURNING id
    """, (proxy_type, host, port, username, password_encrypted))
    
    proxy_id = cur.fetchone()[0]
    conn.commit()
    
    print(f"\n✅ Proxy añadido con éxito (ID: {proxy_id})")
    print(f"   Contraseña encriptada: {password_encrypted[:50]}...")
    
    cur.close()
    conn.close()

def main():
    """Menú principal"""
    print("=" * 60)
    print("  WAIFUGEN - INGESTA SEGURA DE DATOS")
    print("  Todas las contraseñas se encriptan con AES-256")
    print("=" * 60)
    
    while True:
        print("\n¿Qué deseas hacer?")
        print("  1. Añadir cuenta de red social")
        print("  2. Añadir proxy")
        print("  3. Salir")
        
        choice = input("\nOpción: ").strip()
        
        if choice == "1":
            add_account()
        elif choice == "2":
            add_proxy()
        elif choice == "3":
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")

if __name__ == "__main__":
    main()
