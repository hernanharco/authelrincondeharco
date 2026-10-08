"""
backend/app/core/crypto.py
Gestión de claves RSA para JWT RS256 + JWKS.

Provee:
- Carga/generación automática de par RSA
- Conversión a formato JWKS para consumo por clientes
"""

import base64
import logging
import time
from pathlib import Path
from typing import Tuple, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# Directorio donde se almacenan las claves (relativo al backend/)
KEYS_DIR = Path(__file__).resolve().parent.parent.parent / "keys"


# ── Generación y persistencia ─────────────────────────────────


def _ensure_keys_dir():
    """Asegura que el directorio de claves existe."""
    KEYS_DIR.mkdir(parents=True, exist_ok=True)


def _generate_rsa_private_key() -> rsa.RSAPrivateKey:
    """Genera un par de claves RSA de 2048 bits."""
    return rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )


def _save_private_key(private_key: rsa.RSAPrivateKey, path: Path):
    """Guarda clave privada en PEM (PKCS#8, sin encriptar)."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    path.write_bytes(pem)


def _save_public_key(private_key: rsa.RSAPrivateKey, path: Path):
    """Guarda clave pública en PEM (SubjectPublicKeyInfo)."""
    public_key = private_key.public_key()
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    path.write_bytes(pem)


def load_or_generate_keys(
    private_key_path: Optional[Path] = None,
    public_key_path: Optional[Path] = None,
) -> Tuple[str, str]:
    """
    Carga el par RSA desde archivos, o lo genera si no existe.

    Returns:
        (private_key_pem: str, public_key_pem: str)
    """
    private_key_path = private_key_path or KEYS_DIR / "private.pem"
    public_key_path = public_key_path or KEYS_DIR / "public.pem"

    if private_key_path.exists() and public_key_path.exists():
        logger.info("🔑 Claves RSA encontradas en %s", KEYS_DIR)
        private_pem = private_key_path.read_bytes()
        public_pem = public_key_path.read_bytes()
    else:
        logger.info("🔑 Generando nuevo par de claves RSA en %s...", KEYS_DIR)
        _ensure_keys_dir()
        private_key = _generate_rsa_private_key()
        _save_private_key(private_key, private_key_path)
        _save_public_key(private_key, public_key_path)
        private_pem = private_key_path.read_bytes()
        public_pem = public_key_path.read_bytes()
        logger.info("✅ Claves RSA generadas y guardadas en %s", KEYS_DIR)

    return private_pem.decode("utf-8"), public_pem.decode("utf-8")


# ── JWKS ──────────────────────────────────────────────────────


def _base64url_encode(data: bytes) -> str:
    """Base64url sin padding (según RFC 7515)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def build_jwks(public_key_pem: str, key_id: str = "authcore-key-1") -> dict:
    """
    Convierte una clave pública RSA (PEM) a formato JWKS.

    Returns:
        Diccionario JWKS listo para serializar como JSON.
        Ej: {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", ...}]}
    """
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode("utf-8"), backend=default_backend()
    )

    if not isinstance(public_key, rsa.RSAPublicKey):
        raise TypeError("La clave pública no es RSA")

    numbers = public_key.public_numbers()

    # Longitud en bytes del módulo
    n_bytes = numbers.n.to_bytes((numbers.n.bit_length() + 7) // 8, byteorder="big")
    e_bytes = numbers.e.to_bytes((numbers.e.bit_length() + 7) // 8, byteorder="big")

    return {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": key_id,
                "n": _base64url_encode(n_bytes),
                "e": _base64url_encode(e_bytes),
            }
        ]
    }


# ── Singleton cache ───────────────────────────────────────────

_keys_cache: Optional[Tuple[str, str]] = None


def get_rsa_keys() -> Tuple[str, str]:
    """Singleton: carga las claves una sola vez."""
    global _keys_cache
    if _keys_cache is None:
        _keys_cache = load_or_generate_keys()
    return _keys_cache


def get_private_key() -> str:
    """Obtiene la clave privada PEM."""
    return get_rsa_keys()[0]


def get_public_key() -> str:
    """Obtiene la clave pública PEM."""
    return get_rsa_keys()[1]


# ── JWKS cache con TTL ───────────────────────────────────────
# La clave pública NO cambia a menos que se regeneren las claves RSA.
# Podemos cachear el JWKS por 1 hora sin problema.

_jwks_cache: Optional[Tuple[dict, float]] = None
JWKS_CACHE_TTL_SECONDS = 3600  # 1 hora


def get_jwks() -> dict:
    """
    Obtiene el JWKS actual con cache de 1 hora (TTL).
    La clave pública RSA no cambia entre requests, no tiene sentido
    reconstruir el JWKS en cada llamado a /.well-known/jwks.json.
    """
    global _jwks_cache
    now = time.time()

    if _jwks_cache is not None:
        cached_jwks, timestamp = _jwks_cache
        if now - timestamp < JWKS_CACHE_TTL_SECONDS:
            return cached_jwks

    jwks = build_jwks(get_public_key())
    _jwks_cache = (jwks, now)
    return jwks
