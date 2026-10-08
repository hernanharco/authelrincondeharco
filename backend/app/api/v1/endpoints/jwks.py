"""
Endpoint /.well-known/jwks.json
Expone la clave pública RSA en formato JWKS estándar (RFC 7517).

Los proyectos cliente (Portfolio, Tapicería, etc.) usan este endpoint
para obtener la clave pública y verificar los JWT emitidos por authCore.
"""

from fastapi import APIRouter
from app.core.crypto import get_jwks

router = APIRouter()


@router.get("/.well-known/jwks.json", include_in_schema=False)
async def jwks_endpoint():
    """
    Retorna el JWKS (JSON Web Key Set) con la clave pública RSA.
    Los clientes usan esta clave para verificar JWT firmados por authCore.
    """
    return get_jwks()
