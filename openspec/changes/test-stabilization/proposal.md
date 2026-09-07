# Proposal: Test Stabilization (authCore, Fase 1)

## Intent
Backend 109/115 tests skipped + frontend 84 vitest tests unrunnable after the auth refactor (async SQLAlchemy, httpOnly cookies, new domain API). Coverage 56.82% < gate 80% blocks delivery confidence. Re-activate both suites against current architecture and fix the 2 prod defects they expose.

## Scope
**In**
- Backend: rewrite 8 test files low→high risk (domain, models, token/google, auth, user services, user repo, auth endpoints, user endpoints, main); drop invalid tests (e.g., `test_user_validation`).
- Prod fixes (minimal): add `search_users` + `get_user_activity_summary` to IUserRepository/UserRepository; align `/users/pending` service check to admin+; DELETE `/users/{id}` returns deleted user (physical), no false 404.
- conftest: slowapi `DisabledLimiter` override for endpoint suites.
- Frontend: `pnpm install`; setup.ts drop `@sveltejs/kit/vite`; svelte plugin in vitest.config; rewrite 7 suites vs httpOnly cookies; extract pure utils (JWT parse/expiry, `canAccessDashboard`).
- Tests encode decisions: physical delete; pending = admin+; stats keys (`total/by_role/by_status/by_origin/locked_accounts/new_this_week`); limiter override.

**Out**: new features, E2E, Hetzner/deploy, migrations, soft delete, superadmin-only pending, schema changes.

## Capabilities
**New**
- `user-repository-extended`: `search_users(query, limit)` + `get_user_activity_summary(user_id)` contract (interface + impl; shape per `UserActivitySummary` schema).
- `user-admin-api`: physical DELETE semantics, pending admin+ guard, stats shape, functional search/activity endpoints.
- `frontend-test-infrastructure`: vitest runnable on cookie-era components; pure utils extraction.

**Modified**: None (openspec/specs/ empty).

## Approach
Rewrite in place per exploration order; TDD loop `pytest -q --no-cov` (coverage gate blocks full run). Frontend infra-first, then suites; unit-test pure utils over Astro middleware runtime. Forecast >400 lines → chained PRs (work units: prod fixes, backend suites, frontend infra, frontend suites).

## Affected Areas
| Area | Impact |
|---|---|
| backend/tests/*.py (8) + conftest.py | Rewritten/Modified |
| backend/app/interfaces/user/IUserRepository.py | +2 methods |
| backend/app/repositories/UserRepository.py | Implement search/activity |
| backend/app/services/user/UserQueryService.py | Pending → admin+ |
| backend/app/api/v1/endpoints/users.py | DELETE returns deleted user |
| frontend/tests/**, setup.ts, vitest.config.ts, package.json | Rewritten/Modified |
| frontend/src/lib/utils (new) | Pure logic extraction |

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| 429 rate limit on /login suites | High | Limiter override |
| 80% coverage gate blocks run | High | `--no-cov` in TDD loop |
| Final test count ≠ 109 | Med | Documented removals, intent kept |
| DELETE response fix beyond named scope | Med | Confirm in question round |
| RSA keys side effect (backend/keys/) | Low | Accept in repo |

## Rollback Plan
Per-slice git revert (tests-only slices safe). Prod fixes isolated in one slice; revert independently. No migrations/data touched.

## Dependencies
- `pnpm install` (node_modules absent); add `@sveltejs/vite-plugin-svelte` devDep.

## Success Criteria
- [ ] Backend suite green via `pytest -q --no-cov`, module skips removed.
- [ ] `pnpm test:run` green after infra fix.
- [ ] `/users/search` and `/users/{id}/activity` → 200 (no AttributeError).
- [ ] DELETE → returns deleted user; GET after → 404.
- [ ] ADMIN `/users/pending` → 200; USER → 403.

## Proposal Question Round
1. DELETE response: 200 with deleted-user body, or 204?
2. Pending fix = one-line prod change (`validate_admin_permission`) — OK?
3. Dropping invalid tests (e.g., `test_user_validation`) allowed?
4. New frontend pure-utils files OK?