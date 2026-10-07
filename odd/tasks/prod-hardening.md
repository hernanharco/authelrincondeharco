# Feature: Prod Hardening (Fase 3)

**Status:** done (Fase 3 completa)
**Source:** backlog de Fase 1/2 + decisiones de producto del usuario
**Started:** 2026-10-07

## Decisions (user-confirmed, 2026-10-07)

1. **Rate limiting → Redis** (producción seria): slowapi `storage_uri` configurable, `redis://` en prod, `memory://` como fallback dev/test. Redis como servicio en compose.
2. **Login tradicional setea cookie `access_token` httpOnly** (fix): `POST /auth/login` pasa a setear la cookie igual que el callback Google; respuesta JSON se mantiene (backward compatible).
3. **Sesión 120 min** (se mantiene el actual `ACCESS_TOKEN_EXPIRE_MINUTES=120` — sin cambio).

## Tasks

- [x] **H1 — Redis rate limit**: `RATELIMIT_STORAGE_URI` (default memory://), `storage_uri` en Limiter, redis ^8.1.0, servicios redis en compose.prod (healthcheck+volume) y compose.yaml (dev), docs README.
- [x] **H2 — Cookie en login**: TDD — tests primero (worker capturó RED, timeout del worker), guard `if False` eliminado en recuperación, GREEN 26/26. Cookie idéntica a Google callback.
- [x] **H3 — Verificación**: import OK sin Redis; **240 tests / 0 failed / 0 skipped, coverage 87.04% gate PASS**; compose `config -q` OK (ambos); frontend 107 ✅.

## Follow-up (post-review R4)

- [x] **H4 — Redis runtime degradation**: `ResilientStorage` (esquema `redis-fallback://`) en ratelimit.py + 12 tests (TDD: RED ImportError/caracterización, GREEN 12). 252 tests / 0 failed / 86.66% gate. Commit: (ver Evidence).

## Evidence (commits)

- Evidence: `b0cbea8` feat: harden session cookie and rate-limit storage
- Evidence H4: `22d17ad` fix: degrade rate limiting to memory when Redis is unreachable
- Review RDD: `review-2c1c644e76fb494b` → **APPROVED** (tier medium, lens reliability, ack quemado). Advisory no bloqueantes: R3-001 WARNING ratelimit.py:200, R3-002 SUGGESTION ratelimit.py:186 (backlog). Linaje previo `review-d627b2421ce0c735` (alto, 4 lenses) quedó escalated/stop por fallo de transporte en reliability — su finding R4 motivó H4.

## Incidentes

- Worker `muxoh8p9` timeout (30 min bash colgado por fsync): código quedó escrito; guard RED `if False` eliminado y poetry lock resuelto en recuperación inline.
- **Sesión paralela** escribió `data_token.py` + `test_data_token.py` + `auth/__init__.py` durante la fase (carrera en test.db causó failures transitorios); NO commiteados aquí. Sus 11 tests: verdes.
- Backlog: `backend/poetry.lock` en .gitignore (sin build reproducible); Redis runtime no ejercitado (solo lazy import).

## Success Criteria

- [x] `POST /auth/login` → response incluye `Set-Cookie: access_token=…; HttpOnly` ✅
- [x] Ratelimit storage configurable vía env; default memory (tests sin Redis) ✅
- [x] compose.prod.yaml define servicio redis ✅ (config -q OK)
- [x] Backend: 0 failed/0 skipped, gate pass (240/87.04%); frontend 107 pass ✅
