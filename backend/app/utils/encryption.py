"""
File encryption utilities for secure document storage
"""

import os
from cryptography.fernet import Fernet
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Generate or load encryption key
_key = None


def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    global _key
    if _key is None:
        key_file = os.path.join(settings.UPLOAD_DIR, ".encryption_key")
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                _key = f.read()
        else:
            _key = Fernet.generate_key()
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            with open(key_file, "wb") as f:
                f.write(_key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
    return _key


def encrypt_file(file_path: str) -> str:
    """
    Encrypt a file and save encrypted version
    
    Returns:
        Path to encrypted file
    """
    if not settings.ENCRYPT_FILES:
        return file_path
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        # Read original file
        with open(file_path, "rb") as f:
            file_data = f.read()
        
        # Encrypt
        encrypted_data = fernet.encrypt(file_data)
        
        # Save encrypted file
        encrypted_path = file_path + ".encrypted"
        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)
        
        # Remove original (in production, consider keeping both)
        # os.remove(file_path)
        
        return encrypted_path
    except Exception as e:
        logger.error(f"Error encrypting file {file_path}: {e}")
        return file_path


def decrypt_file(encrypted_path: str, output_path: str) -> str:
    """
    Decrypt a file
    
    Returns:
        Path to decrypted file
    """
    if not settings.ENCRYPT_FILES:
        return encrypted_path
    
    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        
        # Read encrypted file
        with open(encrypted_path, "rb") as f:
            encrypted_data = f.read()
        
        # Decrypt
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Save decrypted file
        with open(output_path, "wb") as f:
            f.write(decrypted_data)
        
        return output_path
    except Exception as e:
        logger.error(f"Error decrypting file {encrypted_path}: {e}")
        raise





