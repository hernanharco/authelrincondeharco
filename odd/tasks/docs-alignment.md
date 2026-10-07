# Feature: Docs Alignment (Fase 2)

**Status:** done (Fase 2 completa)
**Source:** reporte de revisión inicial (README/AGENTS desactualizados vs código)
**Started:** 2026-10-07
**Predecesora:** Fase 1 test-stabilization (completa, 6 commits en dev)

## Context

La documentación quedó atrás del código: multi-tenant ya está implementado pero figura como "próximas features", la cookie se llama `access_token` (no `token`), JWT expira a 120 min (no 30), Python 3.12 (no 3.10), y el frontend/README sigue siendo el starter de Astro.

## Tasks

- [x] **D1 — README.md raíz**: multi-tenant a características, endpoints reales (corrige: jwks es `/.well-known/jwks.json`, tenant-modules con guión, user_tenants bajo `/users`), cookie `access_token`/120min, Python 3.10+ (pyproject ^3.10, runtime 3.12), estado 227/107/86.22%.
- [x] **D2 — AGENTS.md**: cookie `access_token` httpOnly 120min (Lax dev / None+Secure prod), solo Google callback la setea, `python -m pytest` + gate activo.
- [x] **D3 — frontend/README.md**: reescrito (68 líneas, español) — comandos, estructura, 9 suites, env vars reales (PUBLIC_BACKEND_URL, API_TARGET, SITE_ORIGIN; PUBLIC_GOOGLE_CLIENT_ID NO existe en frontend).
- [x] **D4 — openspec**: success criteria tildados con números reales + sección Outcome; change movido a `openspec/changes/archive/test-stabilization/`.
- Correcciones al fact list: sin `pnpm check`, sin `create_test_user.py`, sin logout backend, tests en `frontend/tests/`.

## Decisions

- Revisión de README: solo hechos verificados contra código (nada de inventar behavior).
- Los bugs conocidos NO se documentan como features (van a backlog, no a README).

## Evidence (commits)

- Evidence: `fb6e083` docs: align README, AGENTS and frontend README with real code

## Success Criteria

- [x] README sin afirmaciones obsoletas (grep multi-tenant/3.10/30 min/`token` cookie) ✅ (grep sin hits)
- [x] AGENTS.md refleja cookie real y cómo correr tests ✅
- [x] frontend/README no es el starter ✅ (reescrito)
- [x] openspec change archivada con resultados ✅

## Follow-ups (pendientes)
- Formato de `openspec/specs/` para las 3 capabilities — sin ejemplos, requiere decisión humana/plantilla.
- `openspec/config.yaml` testing.backend.coverage todavía cita `tests/pytest.ini` (inerte).
