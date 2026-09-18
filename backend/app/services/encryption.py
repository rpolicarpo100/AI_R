from cryptography.fernet import Fernet
from ..core.config import settings
import os
import base64

def get_fernet():
    key = settings.ENCRYPTION_KEY
    if not key:
        # Try to read existing key file for persistence (rigor)
        try:
            if os.path.exists(".fernet_key"):
                with open(".fernet_key", "r") as f:
                    file_key = f.read().strip()
                    if file_key and len(file_key) >= 40:
                        key = file_key
        except:
            pass
        
        if not key:
            # Generate and persist for dev
            key = Fernet.generate_key().decode()
            try:
                with open(".fernet_key", "w") as f:
                    f.write(key)
            except:
                pass
    else:
        if len(key) < 40:
            key = base64.urlsafe_b64encode(key.ljust(32)[:32].encode()).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)

fernet = get_fernet()

def encrypt_api_key(plain: str) -> str:
    if not plain:
        return ""
    return fernet.encrypt(plain.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    if not encrypted:
        return ""
    try:
        return fernet.decrypt(encrypted.encode()).decode()
    except Exception:
        # Fallback for unencrypted legacy
        return encrypted

def mask_api_key(encrypted_or_plain: str) -> str:
    """Never expose full key to frontend. Returns sk-...****"""
    try:
        plain = decrypt_api_key(encrypted_or_plain)
    except:
        plain = encrypted_or_plain
    if len(plain) <= 8:
        return "****"
    return f"{plain[:4]}...{plain[-4:]}"
