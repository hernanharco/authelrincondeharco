# Exploration: Fase 1 Test Stabilization (authCore)

## Current State

- Backend: 115 tests collected → **6 passed / 109 skipped / 0 failed**. Coverage 56.82% < gate 80%.
  Skip via module-level `pytestmark` "Necesita reescritura post-estabilización (Fase 1)" in 7 files + 1
  individual skip (`test_google_callback_success`, issue #8).
- Per-file counts:

  | File | Tests | Status |
  |------|------:|--------|
  | test_auth_endpoints.py | 7 | 6 pass / 1 skip (issue #8) |
  | test_domain.py | 20 | all skip |
  | test_models.py | 14 | all skip |
  | test_auth_services.py | 15 | all skip |
  | test_user_endpoints.py | 19 | all skip |
  | test_user_repository.py | 19 | all skip |
  | test_user_services.py | 18 | all skip |
  | test_main.py | 3 | all skip |

- `conftest.py` harness is **validated working**: aiosqlite engine + StaticPool, `get_db` override,
  autouse `db` fixture recreates tables per test, async `client` (httpx.ASGITransport) and
  `db_session` fixtures. The 6 passing endpoint tests already exercise it.
- Frontend: vitest suite (**84 tests**: middleware 12, authService 12, login page 14,
  GoogleButton 10, LoginForm 10, StatsCard 10, UsersTable 16) is **NOT runnable**:
  - `node_modules` absent; `pnpm test:run` requires install first.
  - `tests/setup.ts` imports `@sveltejs/kit/vite` — NOT installed (only a peer-dep mention in
    pnpm-lock); import would fail after install.
  - `vitest.config.ts` has no Svelte/Vite plugin configured (only `@sveltejs/vite-plugin-svelte`
    exists transitively via `@astrojs/svelte`) — `.svelte` components can't compile in vitest.
  - `tests/setup.ts` contains a full pasted vitest config (duplicate of vitest.config.ts).

## Affected Areas

- `backend/tests/*.py` (8 files) — all must be rewritten against current async APIs.
- `backend/tests/conftest.py` — harness OK; may need rate-limit override for /login tests.
- `frontend/tests/**` (7 files) + `frontend/tests/setup.ts` + `frontend/vitest.config.ts` —
  infra fix + rewrite against cookie-based reality.
- `frontend/package.json` — dependency adjustments (remove @sveltejs/kit import need; maybe add
  `@sveltejs/vite-plugin-svelte` devDep).

## API Drift (tests vs production) — root cause of skips

### Domain / Models (pure)
- `UserDomain.is_active()` / `is_locked()` no longer exist → replaced by `is_authenticated()`,
  `is_pending_approval()`, `can_login()`. Old tests call the removed methods (AttributeError).
- `can_assign_role` semantics changed: only SUPERADMIN can assign SUPERADMIN/ADMIN; old tests
  expect admin→ADMIN True and manager→USER True (both now False).
- `can_delete(target)`, `is_superadmin()`, `is_admin()`, `is_manager_or_above()` intact.
- `User` model: `role` default USER, `status` default PENDING, `is_active` default False,
  `full_name` NOT NULL; `__repr__` shows only username+role (old test expects email too);
  no constructor validation (SQLAlchemy validates at flush, not `__init__`) —
  `test_user_validation` is invalid as written.

### Services
- `TokenService`: `create_token()`/`verify_token()` (sync, legacy names) → now
  `async create_access_token(data, expires_delta=None) -> (token, datetime)` and
  `async verify_token(token)`. Old tests are sync + wrong names.
- `GoogleOAuthService`: legacy `get_user_info(code, redirect_uri)` → now `exchange_code(code,
  redirect_uri)`, `verify_token(token)`, `get_user_info(token)`. Old mocks patch a dead signature.
- `AuthService`: constructor `(token_service, oauth_service, user_repository)` matches; but no
  `.db` attribute anymore (old tests do `auth_service.db.add(...)` → AttributeError).
  `process_google_login(email, full_name, username)` → now `(code, redirect_uri)`; new users
  raise HTTPException 403 `PENDING_APPROVAL` (no token returned).
- `UserService`: constructor `(db, user_repository)` matches; **every method now requires
  `current_user`**; `delete_user` returns repo result (User or None), not bool; `get_stats`
  shape changed.
- `UserRepository`: 100% async. `get_stats` keys: `total`, `by_role`, `by_status`, `by_origin`,
  `locked_accounts`, `new_this_week` (old tests: `total_users`/`active_users`/`pending_users`).
  `delete()` is PHYSICAL `db.delete` (old tests assume soft delete with `is_active=False`).

### Extra production drift (out of scope, documented)
- `UserQueryService` calls `user_repository.search_users()` and
  `user_repository.get_user_activity_summary()` which exist in NEITHER `IUserRepository` NOR
  `UserRepository` → `/users/search` and `/users/{id}/activity` would raise AttributeError.
- `/users/pending`: endpoint guard is admin+ but service calls
  `validate_superadmin_permission` → ADMIN gets 403 (inconsistency).
- `DELETE /users/{id}`: physical delete then re-fetch via `get_user_by_id` → 404; contradicts
  the endpoint's soft-delete comment.
- `/` message changed ("✅ Backend está corriendo correctamente" vs "AuthCore API is running");
  `/info` endpoint removed; `/health` shape changed.
- `create_access_token(subject=...)` — old fixtures pass `data={...}` → TypeError.
- `/login` rate-limited 10/minute (slowapi) → repeated login tests may hit 429.

### Frontend drift (localStorage → httpOnly cookies migration)
- `middleware.ts` (real): imports `astro:middleware` virtual module (unresolvable in vitest
  without Astro plugin), uses `context.cookies` + `context.redirect(url, 302)`. Old tests:
  fictional localStorage + `Astro.redirect('/login')`.
- `authService.ts` (real): class `AuthService` with `login(credentials)`, `getCurrentUser()`,
  private `handleResponse`, `fetch` with `credentials: 'include'`. Old tests: module-level
  functions (`logout`, `isAuthenticated`, `getToken`, `makeAuthenticatedRequest`, `refreshToken`,
  `isValidToken`, `setAuthLoading`...) that don't exist.
- `GoogleButton.svelte` (real): `window.top.location.replace(BACKEND_URL + /api/v1/auth/google)`,
  text "Continuar con Google", loading "Conectando...", no aria-label. Old tests: popup
  `window.open` + postMessage + localStorage `session`.
- `LoginForm.svelte` (real): labels "Nombre de usuario"/"Contraseña", button "Entrar al sistema",
  HTML `required` only (no custom messages), no password toggle. Old tests: "Username"/"Password",
  "Iniciar Sesión", custom validation messages, toggle button, "Iniciando sesión...".
- `StatsCard.svelte` (real): props `title`, `value`, optional `iconName`, `trend`, `color`
  (`primary|success|warning|danger|muted`); no testids, no number formatting, no
  role="article"/aria-label. Old tests: `icon`/`color` strings, testids `stats-card`/`stats-icon`,
  fixed Tailwind classes, `1.23M` formatting.
- `UsersTable.svelte` (real): props `users`, `onUserUpdate`, `onUserDelete`, `onUserLock`;
  filtering/pagination INTERNAL. Old tests: `loading`, `onFilter`, `onSort`, `onPageChange`,
  `selectable`, "Página 1 de 3", row checkboxes, "Editar"/"Bloquear" buttons.
- `login.test.ts`: renders fake HTML strings (`render(() => '<div>...')`) — tests nothing real.

## Approaches

1. **Rewrite tests in place per layer** (recommended) — keep files and intent, update to current
   async APIs; no production changes except minimal defects blocking intended behavior.
   Effort: Medium-High (84 frontend + 108 backend tests touched).
2. **Delete-and-recreate backend suites** — cleaner history, same effort, loses prior intent.
   Effort: Medium-High.
3. **Frontend: infra-first** — fix deps/setup/plugin (make suite runnable), then rewrite suites
   against cookie reality; extract pure logic (JWT parse/expiry, `canAccessDashboard`) into utils
   to unit-test without Astro runtime. Effort: Medium.

## Recommendation

Backend: rewrite in place, layer order (low→high risk):
1. `test_domain.py` (pure unit, no DB)
2. `test_models.py` (pure unit)
3. `test_auth_services.py` (Token/GoogleOAuth/AuthService with mocked repos)
4. `test_user_services.py` (mock repo + `current_user`)
5. `test_user_repository.py` (async DB via `db_session`, aiosqlite)
6. `test_auth_endpoints.py` (rewrite `test_google_callback_success` for issue #8 new flow)
7. `test_user_endpoints.py` (persist users, role guards, stats shape, delete semantics)
8. `test_main.py` (root/health shapes)

Frontend: fix infra first (setup.ts no @sveltejs/kit, svelte plugin in vitest.config, jest-dom,
pnpm install), then rewrite suites against cookie-based components; prefer unit-testing pure
utils over Astro runtime middleware.

## Risks

- slowapi RateLimitExceeded (429) on /login tests without limiter override in conftest.
- Coverage gate `--cov-fail-under=80` blocks full run today; use `pytest -q --no-cov` in TDD loop.
- Product decisions tests must encode: physical vs soft delete, pending-guard (superadmin vs
  admin), stats shape, login rate limit — may need minimal production fixes (consensus in proposal).
- `search_users`/`get_user_activity_summary` already broken in prod (interface drift) — out of scope.
- RSA keys auto-generated into `backend/keys/` during tests (side effect).
- `GoogleOAuthService` opens `httpx.AsyncClient` per instance, never closed (resource warnings).

## Ready for Proposal

**Yes** — orchestrator should tell the user: change name `test-stabilization`, scope backend 8
files + frontend 7 files + infra deps, no prod changes unless a spec'd minimal fix for
delete/stats/pending-guard is accepted, delivery likely >400 lines → plan chained PRs.