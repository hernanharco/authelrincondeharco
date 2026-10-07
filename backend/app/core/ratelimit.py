"""
Rate Limiting para authCore.
Usa slowapi con almacenamiento configurable via `storage_uri`
(settings.ratelimit_storage_uri / env RATELIMIT_STORAGE_URI):
- "memory://" (default): dev y tests, sin dependencias externas (sin envolver).
- "redis://" (y demás URIs servidas por RedisStorage de limits): producción
  (contador compartido entre instancias/restarts), envueltas en
  `ResilientStorage` para degradar a contadores en memoria si Redis no está
  accesible en runtime (nunca un 500 por storage caído; ver R4).
La conexión a Redis es perezosa (limits la abre al primer uso), así que
importar este módulo no requiere un servidor Redis en marcha.

Protege endpoints críticos como /login contra ataques de fuerza bruta.
"""

import logging
import urllib.parse
from typing import Any

from limits.errors import ConfigurationError, StorageError
from limits.storage import MemoryStorage, RedisStorage, Storage, storage_from_string
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings

logger = logging.getLogger("authCore.ratelimit")


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


# ── Storage resiliente (R4: sin degradación a 500 cuando Redis cae) ──────────

_FALLBACK_SCHEME = "redis-fallback"
# La autoridad es un marcador de posición: la URI real va en la opción
# `primary_uri` (así no hay que reconstruir el scheme original).
_FALLBACK_URI = f"{_FALLBACK_SCHEME}://resilient"
# Esquemas que limits despacha a RedisStorage (misma clase, mismo modo de fallo).
_REDIS_SCHEMES = frozenset(RedisStorage.STORAGE_SCHEME)


def _build_storage_config(storage_uri: str) -> tuple[str, dict[str, str]]:
    """Devuelve (storage_uri, storage_options) para el Limiter de slowapi.

    Si la URI está servida por RedisStorage de limits (redis://, rediss://,
    redis+unix://, valkey://…), la envolvemos mediante el scheme custom
    `redis-fallback://` pasando la URI original como `primary_uri`. Cualquier
    otra URI (en particular el default `memory://`) se devuelve intacta para
    que dev/tests se comporten exactamente igual que hasta ahora.
    """
    if urllib.parse.urlparse(storage_uri).scheme in _REDIS_SCHEMES:
        return _FALLBACK_URI, {"primary_uri": storage_uri}
    return storage_uri, {}


def _storage_error_types(primary: Storage) -> tuple[type[Exception], ...]:
    """Errores de storage que activan la degradación a memoria.

    - Errores de conexión/temporización a nivel de socket de Python.
    - Los que el primario declara en `base_exceptions` (la clasificación que
      limits itself usa para fallos de storage; p.ej. redis.ConnectionError /
      redis.TimeoutError / redis.RedisError).
    - `limits.errors.StorageError` si el primario envuelve excepciones
      (`wrap_exceptions=True`).
    """
    types: list[type[Exception]] = [ConnectionError, TimeoutError, OSError]
    base = getattr(primary, "base_exceptions", ())
    if isinstance(base, type):
        base = (base,)
    types.extend(t for t in base if isinstance(t, type) and issubclass(t, Exception))
    if getattr(primary, "wrap_exceptions", False):
        types.append(StorageError)
    return tuple(types)


class ResilientStorage(Storage):
    """Wrapper de storage con degradación a memoria ante fallos de Redis.

    Envuelve el storage primario configurado (normalmente ``redis://``) y
    delega cada operación con la siguiente semántica:

    - **Intento por llamada, sin circuit breaker**: se intenta el primario en
      cada operación; si falla con un error de conexión/temporización (o
      cualquier error de ``base_exceptions`` del backend), la operación se
      atiende con un :class:`limits.storage.MemoryStorage` interno y la
      petición continúa. Una sola operación exitosa con el primario basta
      para volver a usarlo: no hay estado de "dead" que recuperar.
    - **Sin reconciliación de contadores**: durante la caída cada proceso
      cuenta en memoria (degradado aceptable); al recuperarse Redis, sus
      contadores siguen los suyos. No se reintentan operaciones perdidas.
    - **Ninguna excepción de storage escapa** al path de la petición: es lo
      que evita el 500 de R4 en endpoints protegidos como POST /auth/login.
    - ``check()`` reporta la salud del primario (``False`` mientras esté
      caído) sin lanzar.

    No se aplica al path ``memory://`` (ver :func:`_build_storage_config`).
    """

    STORAGE_SCHEME = [_FALLBACK_SCHEME]

    def __init__(
        self,
        uri: str,
        primary: Storage | None = None,
        fallback: Storage | None = None,
        **options: Any,
    ) -> None:
        primary_uri: str | None = options.pop("primary_uri", None)
        super().__init__(uri, **options)
        if primary is None:
            if not primary_uri:
                raise ConfigurationError(
                    f"{_FALLBACK_URI} requiere la opción primary_uri "
                    "con la URI real del storage primario"
                )
            primary = storage_from_string(primary_uri, **options)
        self._primary = primary
        self._fallback = fallback if fallback is not None else MemoryStorage()
        self._storage_errors = _storage_error_types(primary)
        # Solo para logging de transiciones; el enrutado es por llamada.
        self._degraded = False

    @property
    def base_exceptions(self) -> tuple[type[Exception], ...]:
        return self._storage_errors

    def _mark_degraded(self, op: str, exc: Exception) -> None:
        if not self._degraded:
            self._degraded = True
            logger.warning(
                "Rate limit storage primario inoperativo en %s (%s: %s); "
                "degradando a contadores en memoria por proceso",
                op,
                type(exc).__name__,
                exc,
            )

    def _mark_recovered(self) -> None:
        if self._degraded:
            self._degraded = False
            logger.info(
                "Rate limit storage primario recuperado; se retoman sus contadores"
            )

    def _call_primary(self, op: str, *args: Any, **kwargs: Any) -> Any:
        try:
            result = getattr(self._primary, op)(*args, **kwargs)
        except self._storage_errors as exc:
            self._mark_degraded(op, exc)
            return getattr(self._fallback, op)(*args, **kwargs)
        self._mark_recovered()
        return result

    def incr(self, key: str, expiry: float, amount: int = 1) -> int:
        return self._call_primary("incr", key, expiry, amount)

    def get(self, key: str) -> int:
        return self._call_primary("get", key)

    def get_expiry(self, key: str) -> float:
        return self._call_primary("get_expiry", key)

    def check(self) -> bool:
        # Salud del primario: False si está caído, pero nunca lanza.
        try:
            return bool(self._primary.check())
        except self._storage_errors as exc:
            self._mark_degraded("check", exc)
            return False

    def reset(self) -> int | None:
        return self._call_primary("reset")

    def clear(self, key: str) -> None:
        return self._call_primary("clear", key)

    def __getattr__(self, name: str) -> Any:
        """Delega los métodos extra de los protocols de limits
        (moving window / sliding window, p.ej. ``acquire_entry``) con la misma
        protección: intento en el primario y, si falla, la misma operación en
        la memoria de respaldo.

        Solo se delegan atributos no definidos en la clase y nunca los que
        empiezan por ``_`` (evita recursión si ``__init__`` falla a medias).
        """
        if name.startswith("_"):
            raise AttributeError(name)
        primary_op = getattr(self._primary, name)
        if not callable(primary_op):
            return primary_op
        fallback_op = getattr(self._fallback, name, None)

        def _guarded(*args: Any, **kwargs: Any) -> Any:
            try:
                return primary_op(*args, **kwargs)
            except self._storage_errors as exc:
                self._mark_degraded(name, exc)
                if fallback_op is None:
                    raise
                return fallback_op(*args, **kwargs)

        return _guarded


_STORAGE_URI, _STORAGE_OPTIONS = _build_storage_config(
    settings.ratelimit_storage_uri
)

# Instancia global del rate limiter
limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=[LIMIT_API_GENERAL],
    storage_uri=_STORAGE_URI,
    storage_options=_STORAGE_OPTIONS,
    enabled=True,
)
