import os
import re
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import jwt
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AURA-Security")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
RAW_SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

DEFAULT_DEV_FALLBACK = "b2984efb34a19b7d87920194857201bc93847562019485720194857201948572"

if ENVIRONMENT == "production":
    if not RAW_SECRET_KEY or RAW_SECRET_KEY == DEFAULT_DEV_FALLBACK:
        raise RuntimeError(
            "FATAL SECURITY CONFIGURATION: In production mode, SECRET_KEY must be set to a unique, "
            "cryptographically secure secret in your environment or .env file."
        )
    SECRET_KEY = RAW_SECRET_KEY
else:
    if not RAW_SECRET_KEY or RAW_SECRET_KEY == DEFAULT_DEV_FALLBACK:
        logger.warning(
            "SECURITY ADVISORY: Using default/ephemeral secret key in development mode. "
            "For production, set a dedicated SECRET_KEY in your .env file."
        )
        SECRET_KEY = RAW_SECRET_KEY or DEFAULT_DEV_FALLBACK
    else:
        SECRET_KEY = RAW_SECRET_KEY

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Enforces password complexity:
    - At least 8 characters
    - Contains at least one digit
    - Contains at least one letter
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters in length."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one numeric digit (0-9)."
    if not re.search(r"[a-zA-Z]", password):
        return False, "Password must contain at least one alphabetical letter."
    return True, ""

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

# ----------------- STRICT FILE VALIDATION ON INGESTION -----------------

ALLOWED_IMAGE_SIGNATURES = {
    "jpeg": b"\xff\xd8\xff",
    "png": b"\x89PNG\r\n\x1a\n",
    "gif": b"GIF8",
    "webp": b"RIFF"  # Note: followed by WEBP at offset 8
}

FORBIDDEN_EXECUTABLE_SIGNATURES = [
    b"MZ",              # Windows PE / EXE / DLL
    b"\x7fELF",         # Linux ELF
    b"\xca\xfe\xba\xbe",# Java class / Mach-O universal
    b"\xfe\xed\xfa",    # Mach-O
    b"#!/bin/",         # Shell script execution header
    b"#!/usr/bin/"
]

def validate_uploaded_image(file_bytes: bytes, filename: str, max_size_bytes: int = 5 * 1024 * 1024) -> Tuple[bool, str]:
    """Validates image upload size, extension, and magic bytes."""
    if len(file_bytes) > max_size_bytes:
        return False, f"File exceeds maximum allowed size of {max_size_bytes // (1024*1024)}MB."
    
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext not in ["jpg", "jpeg", "png", "gif", "webp"]:
        return False, f"File format '.{ext}' is not an authorized image format (use PNG, JPG, or WebP)."
    
    # Verify magic bytes
    if ext in ["jpg", "jpeg"] and not file_bytes.startswith(b"\xff\xd8\xff"):
        return False, "Corrupt or spoofed JPEG file signature."
    elif ext == "png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return False, "Corrupt or spoofed PNG file signature."
    elif ext == "gif" and not (file_bytes.startswith(b"GIF87a") or file_bytes.startswith(b"GIF89a")):
        return False, "Corrupt or spoofed GIF file signature."
    elif ext == "webp":
        if not (file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP"):
            return False, "Corrupt or spoofed WebP file signature."

    return True, ""

def validate_uploaded_artifact(file_bytes: bytes, filename: str, max_size_bytes: int = 15 * 1024 * 1024) -> Tuple[bool, str]:
    """Validates artifact documents and blocks executables/scripts."""
    if len(file_bytes) > max_size_bytes:
        return False, f"Artifact exceeds maximum size of {max_size_bytes // (1024*1024)}MB."

    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    allowed_exts = ["txt", "md", "json", "csv", "py", "pdf", "docx", "png", "jpg", "jpeg", "webp", "html", "yaml", "yml"]
    if ext not in allowed_exts:
        return False, f"File extension '.{ext}' is not permitted in Knowledge Vault."

    # Block executable binaries
    for forbidden in FORBIDDEN_EXECUTABLE_SIGNATURES:
        if file_bytes.startswith(forbidden):
            return False, "Security Violation: Executable binaries and shell scripts are forbidden."

    return True, ""