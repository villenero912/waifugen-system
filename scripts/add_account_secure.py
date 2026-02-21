#!/usr/bin/env python3
"""
Script de Ingesta Segura para WaifuGen
FIX v2: sin contraseña hardcodeada en código
"""

import os
import sys
import psycopg2
from getpass import getpass

sys.path.insert(0, '/app')
from src.utils.security import vault

def connect_db():
    # FIX: sin fallback de contraseña hardcodeada
    password = os.getenv('POSTGRES_PASSWORD')
    if not password:
        raise RuntimeError("POSTGRES_PASSWORD no está configurada en el entorno")

    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'postgres'),
            database=os.getenv('POSTGRES_DB', 'waifugen_prod'),
            user=os.getenv('POSTGRES_USER', 'waifugen_user'),
            password=password,
            port=os.getenv('POSTGRES_PORT', '5432')
        )
        return conn
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        sys.exit(1)

def add_account():
    print("\n🔐 === AÑADIR CUENTA DE RED SOCIAL (SEGURO) ===\n")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM characters ORDER BY id")
    characters = cur.fetchall()

    print("Personajes disponibles:")
    for char_id, name in characters:
        print(f"  {char_id}. {name}")

    character_id = int(input("\nID del personaje: "))

    print("\nPlataformas disponibles:")
    platforms = ["youtube","tiktok","instagram","facebook","line","niconico",
                 "fantia","fc2","fanvue","telegram"]
    for i, p in enumerate(platforms, 1):
        print(f"  {i}. {p}")

    choice = int(input("\nElige plataforma (1-10): ").strip()) - 1
    platform = platforms[choice] if 0 <= choice < len(platforms) else "tiktok"

    username = input("Usuario/Email de la cuenta: ")
    password = getpass("Contraseña (no se mostrará): ")
    password_encrypted = vault.encrypt(password)

    cur.execute("""
        INSERT INTO accounts (character_id, platform, username, password_enc, status, region)
        VALUES (%s, %s, %s, %s, 'active', 'JP')
        RETURNING id
    """, (character_id, platform, username, password_encrypted))

    account_id = cur.fetchone()[0]
    conn.commit()
    print(f"\n✅ Cuenta añadida (ID: {account_id})")
    cur.close()
    conn.close()

def add_proxy():
    print("\n🔐 === AÑADIR PROXY (SEGURO) ===\n")
    proxy_type = input("Tipo (residential/datacenter/mobile): ").lower()
    host = input("Host: ")
    port = input("Puerto: ")
    username = input("Usuario: ")
    password = getpass("Contraseña (no se mostrará): ")
    password_encrypted = vault.encrypt(password)

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO proxies (proxy_type, host, port, username, password_enc, status, region)
        VALUES (%s, %s, %s, %s, %s, 'active', 'JP')
        RETURNING id
    """, (proxy_type, host, port, username, password_encrypted))
    proxy_id = cur.fetchone()[0]
    conn.commit()
    print(f"\n✅ Proxy añadido (ID: {proxy_id})")
    cur.close()
    conn.close()

def main():
    print("="*60)
    print("  WAIFUGEN - INGESTA SEGURA DE DATOS")
    print("="*60)
    while True:
        print("\n1. Añadir cuenta de red social")
        print("2. Añadir proxy")
        print("3. Salir")
        choice = input("\nOpción: ").strip()
        if choice == "1":
            add_account()
        elif choice == "2":
            add_proxy()
        elif choice == "3":
            break

if __name__ == "__main__":
    main()
