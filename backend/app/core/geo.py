"""
Ubicación aproximada de la solicitud de acceso (S2 de pending-request-insight).

Fuente única: las cabeceras del CDN que ya está delante de la API.
`main.py` monta `ProxyHeadersMiddleware` declarando Cloudflare/Dokploy, así que
estas cabeceras llegan desde el edge hasta el contenedor.

`CF-IPCountry` la agrega Cloudflare por defecto en todos los planes.
`CF-IPCity` y `CF-Region` requieren la Managed Transform
"Add visitor location headers" (Rules → Settings → Managed Transforms).
Si una cabecera falta, el campo queda en `None`: nunca se aproxima ni se
completa con una suposición.

Las cabeceras son falsificables por un cliente que llegue directo al proceso,
pero la API sólo escucha en 127.0.0.1 detrás del proxy, y el peor caso es que
un solicitante ensucie su propia fila. No se usan para autorizar nada.
"""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional
from urllib.parse import unquote

from app.core.ratelimit import _get_client_ip

MAX_CITY_LENGTH = 128
MAX_REGION_LENGTH = 128

# Valores que Cloudflare usa para "sin dato" (XX) y Tor (T1).
_UNKNOWN_COUNTRY_CODES = frozenset({"", "XX", "T1"})

_COUNTRY_HEADERS = ("CF-IPCountry", "X-Vercel-IP-Country")
_CITY_HEADERS = ("CF-IPCity", "X-Vercel-IP-City")
# Nombres reales de Cloudflare (Managed Transform "Add visitor location
# headers") y su equivalente en Vercel. No existe un `CF-IPRegion`: la región
# viaja en `cf-region`.
_REGION_HEADERS = ("CF-Region", "X-Vercel-IP-Country-Region")


@dataclass(frozen=True)
class RequestLocation:
    """Ubicación observada en el momento de la solicitud, ya saneada."""

    ip: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None

    def as_user_fields(self) -> Dict[str, Any]:
        """Columnas de `users` que persisten la ubicación de la solicitud."""
        return {
            "last_ip": self.ip,
            "request_country": self.country,
            "request_city": self.city,
            "request_region": self.region,
        }


def empty_location() -> RequestLocation:
    """Ubicación sin datos: solicitudes sin cabeceras de CDN."""
    return RequestLocation()


def _first_header(headers: Mapping[str, str], names: tuple) -> Optional[str]:
    """Primer valor no vacío de `names`, decodificado (Cloudflare url-encodea)."""
    for name in names:
        raw = headers.get(name)
        if not raw:
            continue
        value = unquote(raw).strip()
        if value:
            return value
    return None


def _country_information(headers: Mapping[str, str]) -> Optional[str]:
    raw = _first_header(headers, _COUNTRY_HEADERS)
    if not raw:
        return None
    code = raw.upper()
    if code in _UNKNOWN_COUNTRY_CODES:
        return None
    return code[:2]


def _truncated(value: Optional[str], limit: int) -> Optional[str]:
    if not value:
        return None
    return value[:limit]


def extract_request_location(request: Any) -> RequestLocation:
    """
    Deriva la ubicación de la solicitud desde las cabeceras del CDN.

    Args:
        request: `starlette.requests.Request` (o cualquier objeto con
            `.headers`). `None` devuelve una ubicación vacía: los tests y los
            llamadores internos no están obligados a tener una petición HTTP.

    Returns:
        `RequestLocation` con los campos disponibles; los ausentes en `None`.
    """
    if request is None:
        return empty_location()

    headers = getattr(request, "headers", None)
    if headers is None:
        return empty_location()
    return RequestLocation(
        ip=_client_ip(request),
        country=_country_information(headers),
        city=_truncated(_first_header(headers, _CITY_HEADERS), MAX_CITY_LENGTH),
        region=_truncated(_first_header(headers, _REGION_HEADERS), MAX_REGION_LENGTH),
    )


def _client_ip(request: Any) -> Optional[str]:
    """IP del cliente respetando proxies; nunca rompe la solicitud."""
    try:
        return _get_client_ip(request) or None
    except Exception:  # noqa: BLE001 — la ubicación es un extra, no un requisito
        return None
