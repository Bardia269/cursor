"""Authentification mono-utilisateur, secret de session et protection CSRF."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from ..config import ROOT

SCRYPT_PARAMS = {"n": 2**14, "r": 8, "p": 1}
SECRET_FILE = ROOT / "data" / ".secret_key"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, **SCRYPT_PARAMS)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), **SCRYPT_PARAMS)
    return hmac.compare_digest(digest.hex(), digest_hex)


def secret_key() -> str:
    """SEO_OS_SECRET_KEY, sinon une clé locale générée une fois (mode démo) dans data/.secret_key."""
    key = os.environ.get("SEO_OS_SECRET_KEY")
    if key:
        return key
    if SECRET_FILE.exists():
        return SECRET_FILE.read_text().strip()
    SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(48)
    SECRET_FILE.write_text(key)
    SECRET_FILE.chmod(0o600)
    return key


def csrf_token(session: dict) -> str:
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def csrf_valid(session: dict, provided: str | None) -> bool:
    expected = session.get("csrf")
    return bool(expected and provided and hmac.compare_digest(expected, provided))
