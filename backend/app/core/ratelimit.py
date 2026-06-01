"""
Rate Limiting para authCore.
Usa slowapi con almacenamiento en memoria.
En producción, reemplazar por Redis (slowapi lo soporta via `storage_uri`).

Protege endpoints críticos como /login contra ataques de fuerza bruta.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


def _get_client_ip(request) -> str:
    """
    Obtiene la IP del cliente respetando proxies (Cloudflare, Nginx, Docker).
    slowapi ya considera X-Forwarded-For si está configurado,
    pero esta función asegura que funcione correctamente detrás de proxies.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Tomar la primera IP de la cadena (la real del cliente)
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# ── Límites predefinidos ────────────────────────────────────────
# Formato: "[cantidad]/[ventana_de_tiempo]"
# Ejemplos: "5/minute", "100/hour", "1000/day"

LIMIT_LOGIN = "10/minute"       # Login: máximo 10 intentos por minuto
LIMIT_REGISTER = "3/minute"     # Registro: máximo 3 por minuto
LIMIT_API_GENERAL = "100/minute"  # API general: máximo 100 requests por minuto


# Instancia global del rate limiter
limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=[LIMIT_API_GENERAL],
    enabled=True,
)
