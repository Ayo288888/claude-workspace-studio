import base64
import os
import re
from typing import Optional

# Try importing Fernet from cryptography; provide secure fallback if not yet installed in local env
try:
    from cryptography.fernet import Fernet
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class SessionKeyManager:
    """
    Manages in-memory ephemeral encryption for sensitive user credentials (API Keys).
    Keys are encrypted using a session-unique key in memory and are never persisted to disk.
    """
    def __init__(self, session_secret: Optional[bytes] = None):
        if HAS_CRYPTOGRAPHY:
            self._fernet_key = session_secret or Fernet.generate_key()
            self._cipher = Fernet(self._fernet_key)
        else:
            self._raw_secret = session_secret or os.urandom(32)

    def encrypt_key(self, plain_key: str) -> str:
        """Encrypts a plaintext API key for safe in-memory session holding."""
        if not plain_key:
            return ""
        if HAS_CRYPTOGRAPHY:
            encrypted_bytes = self._cipher.encrypt(plain_key.strip().encode("utf-8"))
            return encrypted_bytes.decode("utf-8")
        else:
            # XOR-based ephemeral cipher fallback when cryptography is loading
            raw_bytes = plain_key.strip().encode("utf-8")
            xor_bytes = bytes([b ^ self._raw_secret[i % len(self._raw_secret)] for i, b in enumerate(raw_bytes)])
            return base64.urlsafe_b64encode(xor_bytes).decode("utf-8")

    def decrypt_key(self, encrypted_token: str) -> str:
        """Decrypts the in-memory token back to plaintext when executing an API request."""
        if not encrypted_token:
            return ""
        try:
            if HAS_CRYPTOGRAPHY:
                decrypted_bytes = self._cipher.decrypt(encrypted_token.encode("utf-8"))
                return decrypted_bytes.decode("utf-8")
            else:
                xor_bytes = base64.urlsafe_b64decode(encrypted_token.encode("utf-8"))
                raw_bytes = bytes([b ^ self._raw_secret[i % len(self._raw_secret)] for i, b in enumerate(xor_bytes)])
                return raw_bytes.decode("utf-8")
        except Exception:
            return ""

def mask_api_key(key: str) -> str:
    """Returns a masked representation of the API key for safe display (e.g. sk-ant-•••••••••••a8F)."""
    if not key:
        return "Not Configured"
    cleaned = key.strip()
    if len(cleaned) <= 12:
        return "••••••••••••"
    prefix = cleaned[:7]
    suffix = cleaned[-4:]
    return f"{prefix}••••••••••••{suffix}"

def validate_anthropic_key(key: str) -> bool:
    """Validates the basic syntax of an Anthropic API key."""
    if not key or not isinstance(key, str):
        return False
    cleaned = key.strip()
    return bool(re.match(r"^sk-ant-[a-zA-Z0-9_\-]{20,}$", cleaned))
