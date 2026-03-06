import os
import base64
import secrets
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger("SecureVault")


def _load_salt() -> bytes:
    """
    Carga el salt de ENCRYPTION_SALT (env var).
    Si no existe, genera uno aleatorio, lo imprime y lanza RuntimeError
    para que el operador lo copie al .env antes de continuar.

    El salt debe ser único por instalación y guardarse de forma permanente.
    Cambiarlo invalida todos los datos encriptados existentes.
    """
    salt_b64 = os.getenv("ENCRYPTION_SALT")
    if salt_b64:
        try:
            return base64.urlsafe_b64decode(salt_b64)
        except Exception:
            raise RuntimeError("ENCRYPTION_SALT tiene formato inválido (debe ser base64).")

    # Primera ejecución: generar salt aleatorio
    new_salt = secrets.token_bytes(32)
    new_salt_b64 = base64.urlsafe_b64encode(new_salt).decode()
    print(
        "\n" + "=" * 60 + "\n"
        "⚠️  ENCRYPTION_SALT no configurado.\n"
        "Añade esta línea a tu .env y vuelve a ejecutar:\n\n"
        f"  ENCRYPTION_SALT={new_salt_b64}\n"
        + "=" * 60 + "\n"
    )
    raise RuntimeError(
        "ENCRYPTION_SALT no configurado. Copia el valor generado arriba al .env."
    )


class SecureVault:
    """
    Gestiona la encriptación y desencriptación de datos sensibles
    usando AES-256 (Fernet) con una clave derivada de ENCRYPTION_KEY
    y un salt único por instalación (ENCRYPTION_SALT).

    Variables requeridas en .env:
        ENCRYPTION_KEY=<contraseña maestra>
        ENCRYPTION_SALT=<base64 de 32 bytes aleatorios — generado en primer arranque>
    """

    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_KEY")
            if not master_key:
                raise RuntimeError("ENCRYPTION_KEY no configurada en .env")

        salt = _load_salt()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200_000,   # ← aumentado de 100k a 200k (OWASP 2024)
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encripta una cadena de texto."""
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Desencripta una cadena de texto. Devuelve cadena de error si falla."""
        if not encrypted_data:
            return ""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            logger.error("SecureVault: fallo al desencriptar. Key o salt incorrecto.")
            return "[ERROR: Decryption Failed]"


# Singleton para uso global — falla rápido si .env no está configurado
try:
    vault = SecureVault()
except RuntimeError as _vault_err:
    # Durante tests o configuración inicial sin .env completo
    vault = None  # type: ignore[assignment]
    logger.warning(f"SecureVault no inicializado: {_vault_err}")

