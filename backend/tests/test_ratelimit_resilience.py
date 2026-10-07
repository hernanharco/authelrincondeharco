"""
Tests de resiliencia del storage de rate limiting (R4-redis-no-runtime-degradation).

Cuando RATELIMIT_STORAGE_URI=redis:// y Redis no está accesible en tiempo de
ejecución, slowapi/limits propaga la excepción de storage y los endpoints
protegidos (p.ej. POST /auth/login) devuelven 500 en vez de degradar
graciosamente a contadores en memoria.

Estos tests son unitarios: sin red y sin Redis vivo (los primarios son dobles
en memoria). Nota: tests/conftest.py desactiva el limiter a nivel de endpoint
en todos los tests (`disable_rate_limiter`, autouse), por eso aquí se ejercita
directamente la capa de storage/estrategia que slowapi usa por debajo de los
endpoints protegidos.
"""

from __future__ import annotations

from typing import Any

import pytest

from limits import parse
from limits.storage import MemoryStorage, RedisStorage, Storage, storage_from_string
from limits.strategies import FixedWindowRateLimiter

from app.core.ratelimit import ResilientStorage, _build_storage_config


class FakeRedisStorage(Storage):
    """Doble de storage 'redis' controlable, sin conexión real.

    - ``exc=None``: primario sano, todas las ops se atienden en el doble.
    - ``exc=ConnectionError|TimeoutError``: falla según ``fail_times``
      (-1 = todas las ops, 0 = ninguna, N = las N primeras ops).
    - ``calls`` registra cada operación intentada, para verificar el enrutado.
    """

    # No participar en el dispatch de scheme de limits (solo el wrapper real).
    STORAGE_SCHEME = None

    def __init__(
        self,
        exc: type[Exception] | None = None,
        fail_times: int = 0,
    ) -> None:
        super().__init__(None)
        self.calls: list[str] = []
        self._exc = exc
        self._fail_times = fail_times
        self._failures = 0
        self._memory = MemoryStorage()

    @property
    def base_exceptions(self) -> tuple[type[Exception], ...]:
        return (ConnectionError, TimeoutError)

    def _maybe_fail(self, op: str) -> None:
        self.calls.append(op)
        if self._exc is None:
            return
        if self._fail_times < 0 or self._failures < self._fail_times:
            self._failures += 1
            raise self._exc("redis caído (simulado)")

    def incr(self, key: str, expiry: float, amount: int = 1) -> int:
        self._maybe_fail("incr")
        return self._memory.incr(key, expiry, amount)

    def get(self, key: str) -> int:
        self._maybe_fail("get")
        return self._memory.get(key)

    def get_expiry(self, key: str) -> float:
        self._maybe_fail("get_expiry")
        return self._memory.get_expiry(key)

    def check(self) -> bool:
        self._maybe_fail("check")
        return True

    def reset(self) -> int | None:
        self._maybe_fail("reset")
        return self._memory.reset()

    def clear(self, key: str) -> None:
        self._maybe_fail("clear")
        return self._memory.clear(key)


def _resilient(primary: Storage) -> ResilientStorage:
    return ResilientStorage("redis-fallback://resilient", primary=primary)


# ── Degradación ante errores de conexión ──────────────────────────────────────


def test_connection_error_degrades_to_memory_counters() -> None:
    """ConnectionError en cada op: todo se atiende en memoria, sin excepción."""
    primary = FakeRedisStorage(exc=ConnectionError, fail_times=-1)
    storage = _resilient(primary)

    assert storage.incr("k", 60) == 1
    assert storage.incr("k", 60) == 2
    assert storage.get("k") == 2
    assert storage.get_expiry("k") > 0
    # La salud reporta al primario caído, pero sin lanzar excepción.
    assert storage.check() is False
    # Cada op llegó al primario antes de degradar (intento por llamada).
    assert primary.calls == ["incr", "incr", "get", "get_expiry", "check"]
    # El contador degradado vive en la memoria local del wrapper.
    assert storage._fallback.get("k") == 2


def test_timeout_error_degrades_to_memory_counters() -> None:
    """TimeoutError en cada op: mismo comportamiento degradado."""
    primary = FakeRedisStorage(exc=TimeoutError, fail_times=-1)
    storage = _resilient(primary)

    assert storage.incr("k", 60) == 1
    assert storage.get("k") == 1
    assert storage.check() is False
    assert primary.calls == ["incr", "get", "check"]


# ── Enrutado con primario sano y recuperación ─────────────────────────────────


def test_healthy_primary_serves_ops_directly() -> None:
    """Con el primario sano, las ops van a él (sin doble conteo en memoria)."""
    primary = FakeRedisStorage()
    storage = _resilient(primary)

    assert storage.incr("k", 60) == 1
    assert storage.incr("k", 60) == 2
    assert storage.check() is True

    assert primary.calls == ["incr", "incr", "check"]
    assert storage._fallback.get("k") == 0


def test_transient_failure_then_recovery_routes_back_to_primary() -> None:
    """Semántica elegida: intento por llamada, sin circuit breaker.

    La 1ª op falla → contador en memoria. La 2ª vuelve a intentar el primario
    (ya sano) y se atiende allí: no hay estado de "dead" que recuperar ni
    reconciliación de contadores (el primario cuenta desde el suyo).
    """
    primary = FakeRedisStorage(exc=ConnectionError, fail_times=1)
    storage = _resilient(primary)

    assert storage.incr("k", 60) == 1  # degradado → memoria
    assert storage.incr("k", 60) == 1  # recuperado → primario (no 2: sin reconciliar)
    assert storage.incr("k", 60) == 2
    assert primary.calls == ["incr", "incr", "incr"]


# ── Nivel estrategia (lo que slowapi ejecuta por request) ─────────────────────


def test_degraded_mode_still_enforces_limits_without_raising() -> None:
    """En modo degradado hit() no lanza y sigue limitando en el proceso."""
    primary = FakeRedisStorage(exc=ConnectionError, fail_times=-1)
    strategy = FixedWindowRateLimiter(_resilient(primary))
    item = parse("3/minute")

    assert [strategy.hit(item, "1.2.3.4", "endpoint") for _ in range(3)] == [
        True,
        True,
        True,
    ]
    assert strategy.hit(item, "1.2.3.4", "endpoint") is False


def test_without_resilient_layer_storage_errors_escape() -> None:
    """Documenta el fallo R4: sin la capa resiliente, el error de Redis escapa
    de la estrategia → slowapi lo propaga → 500 en el endpoint protegido."""
    primary = FakeRedisStorage(exc=ConnectionError, fail_times=-1)
    strategy = FixedWindowRateLimiter(primary)

    with pytest.raises(ConnectionError):
        strategy.hit(parse("10/minute"), "1.2.3.4", "endpoint")


# ── Configuración de la URI y fábrica de limits ───────────────────────────────


@pytest.mark.parametrize(
    "redis_uri",
    [
        "redis://localhost:6379/1",
        "rediss://example.com:6380/0",
        "valkey://localhost:6379/0",
    ],
)
def test_redis_backed_uris_are_wrapped(redis_uri: str) -> None:
    """Las URIs servidas por RedisStorage de limits se configuran envueltas."""
    storage_uri, options = _build_storage_config(redis_uri)
    assert storage_uri == "redis-fallback://resilient"
    assert options == {"primary_uri": redis_uri}


def test_memory_uri_is_untouched() -> None:
    """El path por defecto memory:// (dev/tests) queda idéntico."""
    assert _build_storage_config("memory://") == ("memory://", {})


def test_fallback_scheme_dispatch_builds_resilient_storage() -> None:
    """limits despacha redis-fallback:// a ResilientStorage, que construye su
    primario redis:// de forma perezosa (sin abrir conexión)."""
    storage: Any = storage_from_string(
        "redis-fallback://resilient", primary_uri="redis://localhost:6379/0"
    )

    assert isinstance(storage, ResilientStorage)
    assert isinstance(storage._primary, RedisStorage)


def test_limiter_wiring_does_not_raise_when_redis_is_down() -> None:
    """El Limiter de slowapi construido con la URI resiliente no propaga la
    excepción de storage en su path de evaluación (equivalente unitario de lo
    que ve POST /auth/login con Redis caído)."""
    from slowapi import Limiter

    storage_uri, options = _build_storage_config("redis://localhost:6379/0")
    lim = Limiter(
        key_func=lambda request=None: "1.2.3.4",
        storage_uri=storage_uri,
        storage_options=options,
    )

    assert isinstance(lim._storage, ResilientStorage)
    assert lim._limiter.storage is lim._storage

    # Simular Redis caído "en caliente" tras la construcción:
    lim._storage._primary = FakeRedisStorage(exc=ConnectionError, fail_times=-1)

    assert lim._limiter.hit(parse("10/minute"), "1.2.3.4", "api") is True
