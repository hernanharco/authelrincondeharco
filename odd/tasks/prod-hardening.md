# Feature: Prod Hardening (Fase 3)

**Status:** in_progress
**Source:** backlog de Fase 1/2 + decisiones de producto del usuario
**Started:** 2026-10-07

## Decisions (user-confirmed, 2026-10-07)

1. **Rate limiting → Redis** (producción seria): slowapi `storage_uri` configurable, `redis://` en prod, `memory://` como fallback dev/test. Redis como servicio en compose.
2. **Login tradicional setea cookie `access_token` httpOnly** (fix): `POST /auth/login` pasa a setear la cookie igual que el callback Google; respuesta JSON se mantiene (backward compatible).
3. **Sesión 120 min** (se mantiene el actual `ACCESS_TOKEN_EXPIRE_MINUTES=120` — sin cambio).

## Tasks

- [ ] **H1 — Redis rate limit**: config `RATELIMIT_STORAGE_URI` (default memory://), env redis:// en prod, cliente `redis` como dependencia, servicio redis en compose.prod.yaml (+ compose.yaml dev opcional), docs env.
- [ ] **H2 — Cookie en login**: `login.py` setea `access_token` httpOnly con mismos parámetros que Google callback (max_age=120min, SameSite/Secure por entorno); TDD: test RED primero (Set-Cookie presente + httponly), luego fix, GREEN.
- [ ] **H3 — Verificación**: suite backend verde (227+test nuevo, 0 skipped, gate 80%), frontend 107 verde (no debe romperse: login sigue devolviendo JSON), compose YAML válido.

## Evidence (commits)

- (pendiente)

## Success Criteria

- [ ] `POST /auth/login` → response incluye `Set-Cookie: access_token=…; HttpOnly`
- [ ] Ratelimit storage configurable vía env; default memory (tests sin Redis)
- [ ] compose.prod.yaml define servicio redis
- [ ] Backend: 0 failed/0 skipped, gate pass; frontend 107 pass
