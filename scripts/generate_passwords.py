#!/usr/bin/env python3
"""
Generador de Contraseñas Seguras - Sistema WaifuGen
FIX v2: contraseña maestra no hardcodeada en código
"""

import hashlib
import base64
import argparse
import os
import sys
import secrets
from typing import Dict


class PasswordGenerator:
    def __init__(self, master_password: str):
        self.master_password = master_password.encode('utf-8')

    def generate(self, service_name: str, length: int = 32, iterations: int = 100000) -> str:
        salt = f"waifugen_system_{service_name}_2026".encode('utf-8')
        derived_key = hashlib.pbkdf2_hmac('sha256', self.master_password, salt, iterations, dklen=length)
        password = base64.urlsafe_b64encode(derived_key).decode('utf-8')
        return password.replace('=', '').replace('-', '_')[:length]

    def generate_all(self) -> Dict[str, str]:
        return {
            'POSTGRES_PASSWORD': self.generate('postgres', 40),
            'REDIS_PASSWORD':    self.generate('redis', 40),
            'SECRET_KEY':        self.generate('secret_key', 64),
            'GRAFANA_PASSWORD':  self.generate('grafana', 40),
            'JWT_SECRET':        self.generate('jwt_secret', 64),
            'ENCRYPTION_KEY':    self.generate('encryption', 64),
            # FIX: generar ENCRYPTION_SALT único por instalación
            'ENCRYPTION_SALT':   secrets.token_hex(32),
        }


def main():
    parser = argparse.ArgumentParser(description='Generador de contraseñas WaifuGen')

    parser.add_argument(
        '--master',
        type=str,
        default=None,  # FIX: sin valor por defecto en código
        help='Contraseña maestra (si no se indica, se pide de forma interactiva)'
    )
    parser.add_argument('--output', type=str, help='Guardar en archivo (ej: .env)')
    parser.add_argument('--format', choices=['env', 'table'], default='env')

    args = parser.parse_args()

    # FIX: pedir contraseña de forma interactiva si no se pasa como argumento
    if args.master:
        master = args.master
    else:
        import getpass
        master = getpass.getpass("Introduce la contraseña maestra: ")
        if not master:
            print("❌ La contraseña maestra no puede estar vacía.")
            sys.exit(1)

    generator = PasswordGenerator(master)
    passwords = generator.generate_all()

    if args.output:
        with open(args.output, 'w') as f:
            f.write("# WaifuGen .env — generado automáticamente\n\n")
            for k, v in passwords.items():
                f.write(f"{k}={v}\n")
            f.write("\n# Añade manualmente:\n")
            f.write("A2E_API_ID=\nA2E_API_KEY=\n")
            f.write("REPLICATE_API_TOKEN=\n")
            f.write("TELEGRAM_BOT_TOKEN=\nTELEGRAM_ADMIN_CHAT_ID=\n")
            f.write("INTERNAL_API_KEY=\nPLATFORM_POSTER_API_KEY=\n")
            f.write("THUMBNAIL_SERVICE_API_KEY=\nKARAOKE_API_KEY=\n")
            f.write("RUNPOD_API_KEY=\n")
        print(f"✅ {args.output} creado. Permisos: chmod 600 {args.output}")
    else:
        for k, v in passwords.items():
            if args.format == 'table':
                print(f"{k:<25} {v[:8]}...{v[-8:]}")
            else:
                print(f"{k}={v}")

    print("\n⚠️  IMPORTANTE: guarda la contraseña maestra en un gestor de contraseñas.")
    print("   Nunca la pongas en el código fuente.")


if __name__ == '__main__':
    main()
