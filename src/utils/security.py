import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SecureVault:
    """
    Gestiona la encriptación y desencriptación de datos sensibles
    usando AES-256 (Fernet) con una clave derivada de la ENCRYPTION_KEY.
    """
    
    def __init__(self, master_key: str = None):
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_KEY", "WaifuGen_Insecure_Fallback_Key_2026!")
        
        # Derivar una clave segura de 32 bytes usando PBKDF2
        salt = b'waifugen_salt_production' # En producción idealmente se guardaría aparte
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encripta una cadena de texto"""
        if not data:
            return ""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Desencripta una cadena de texto"""
        if not encrypted_data:
            return ""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return "[ERROR: Decryption Failed]"

# Singleton para uso global
vault = SecureVault()
