# Feature: Test Stabilization (Fase 1)

**Status:** done (Fase 1 completa)
**Source:** openspec/changes/test-stabilization/proposal.md + exploration.md
**Started:** 2025-01-01 · **Cerrada:** mismo día

## Decisions (user-confirmed)

1. `DELETE /users/{id}` → **200 con body del usuario eliminado**.
2. `/users/pending` → **admin+** (una línea en `UserQueryService.validate_admin_permission`).
3. Tests inválidos por diseño (ej. `test_user_validation`) → **eliminar**.
4. Extraer lógica pura del frontend (JWT parse/expiry, `canAccessDashboard`) a **utils nuevos**.

## Tasks

- [x] **T1 — Prod fixes**: `search_users` + `get_user_activity_summary` en `IUserRepository`/`UserRepository`; pending guard → admin+; DELETE devuelve usuario borrado (200). +fix: `IUserService.delete_user` signature aligned (`-> User`, physical delete). Verificado: import OK, `python -m pytest -q --no-cov` → 30 passed / 109 skipped / 0 failed. Nota: `poetry run pytest` falla por sys.path pre-existente (usar `python -m pytest`).
- [x] **T2a — domain+models**: `test_domain.py` 20→27, `test_models.py` 14→14 (−1 inválido), 41 passed / 0 skipped. Contrato nuevo encodeado: solo SUPERADMIN asigna SUPERADMIN/ADMIN; manager no borra. Nota: 2 min por test suite por el fixture autouse de conftest (pre-existente, fuera de alcance).
- [x] **T2b — auth_services + user_services**: 15→34 + 18→24 = 58 passed / 0 skipped. Encodea: 403 PENDING_APPROVAL, borrado físico + race guard 404, stats 6 keys, API async de tokens.
- [x] **T2c — user_repository**: 19→27 passed / 0 skipped. +8 tests nuevos (search, activity summary). Suite completa: 179 collected, 156 passed, 23 skipped restantes.
- [x] **T2d — auth_endpoints + user_endpoints + main**: 7→9 / 19→25 / 3→3. conftest: fixture `disable_rate_limiter`. Suite completa: **187 passed / 0 failed / 0 skipped**. Observaciones prod (para Fase 2/3): login tradicional NO setea cookie (solo JSON), cookie Google max_age=120min no 7d, domain=localhost en dev cookie.
- [x] **T3 — Frontend infra**: pnpm install, svelte plugin vitest (v4/vite5), setup.ts limpio, generate:client + conditions browser. Baseline: **85 tests corren, 83 failed / 2 passed** (drift de asserts → T4). Nota: exploration decía 84, real 85. T4 blockers: require()→ESM en middleware/authService tests; alias `astro:middleware` pendiente cuando se importe via Vite.
- [x] **T4a — utils + auth-layer suites**: `src/utils/jwt.ts` + `guards.ts` extraídos (middleware refactor con paridad byte-a-byte); alias astro:middleware stub en vitest config; suites middleware 13 / authService 14 / login 16 + utils 17 = **60 passed / 0 failed**. Tests inválidos (localStorage, popup OAuth, HTML string) eliminados.
- [x] **T4b — componentes**: GoogleButton 10→6, LoginForm 10→10, StatsCard 10→11, UsersTable 16→20. **Full suite frontend: 107/107 verde** (2 corridas). Intents inválidos (popup, testids, formateo inexistente) eliminados.
- [x] **Cierre**: cobertura 74.49% → **86.22%** (gate ≤431 miss → 297). +40 tests: dev_login (100%, guard 403 prod), google callback +15 branches, CompanyProfileService (100%). Gate activado en pyproject (antes inerte); `core=sysmon` por undercounting de ctrace. 227 tests / 0 failed / 0 skipped.
- [ ] **T4 — Frontend suites + utils**: extraer utils puros (JWT, guards); reescribir 7 suites contra realidad cookies httpOnly.

## Evidence (commits)

- T1: `39aec50` fix: add missing user repository methods and align delete/pending semantics (commit --no-verify por hook de revisión claude sin login, autorizado por usuario)
- T2: `5066527` test: rewrite backend suites against current async APIs (1936+/853−, --no-verify autorizado para la fase)
- T3: `6b82ad0` test: make frontend vitest suite runnable (--no-verify autorizado para la fase)
- T4a: `88bb7f5` test: extract frontend auth utils and rewrite auth-layer suites
- T4b: `614a86d` test: rewrite frontend component suites against real Svelte contracts
- T5 (cobertura): `27015fa` test: raise backend coverage to 86% and activate coverage gate

## Known follow-ups (documented by worker)

- `UserQueryService` llama `get_users_by_role`/`get_active_users_count`/`get_recent_users` que no existen en el repo — dormants (sin endpoint ni delegación), misma clase de defecto que T1. Fuera de alcance de Fase 1.

## Success Criteria

- [x] `pytest -q --no-cov` backend verde sin skips de Fase 1 ✅ (227 passed / 0 skipped, plain `pytest -q` con gate)
- [x] Cobertura ≥ 80% con gate ✅ (86.22%, gate activo en pyproject)
- [x] `pnpm test:run` verde ✅ (107/107, 9 archivos)
- [x] `GET /users/search` y `/users/{id}/activity` → 200 ✅ (test_user_endpoints)
- [x] DELETE → 200 con usuario; GET posterior → 404 ✅
- [x] ADMIN `/users/pending` → 200; USER → 403 ✅

## Notes

- Delivery >400 líneas → work units encadenados, un commit por tarea.
- Branch: `dev` (rama activa del proyecto).
