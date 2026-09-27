import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "b2984efb34a19b7d87920194857201bc93847562019485720194857201948572")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def generate_salt() -> str:
    return secrets.token_hex(16)

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Returns (password_hash, salt)."""
    if not salt:
        salt = generate_salt()
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt

def verify_password(plain_password: str, stored_hash: str, salt: Optional[str] = None) -> bool:
    """Verifies a password against the stored hash and salt with backward compatibility."""
    if not salt:
        # Legacy fallback if salt was not yet populated
        legacy_salt = b"aura_cyberpunk_neural_salt_2026"
        legacy_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), legacy_salt, 100000).hex()
        return secrets.compare_digest(legacy_hash, stored_hash)

    new_hash, _ = hash_password(plain_password, salt)
    return secrets.compare_digest(new_hash, stored_hash)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Encodes a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None