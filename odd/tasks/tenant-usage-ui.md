# Feature: tenant-usage-ui — uso por tenant visible en el frontend

## Contexto

Las métricas de uso por tenant existen solo como queries operativas
(`scripts/tenant-usage.sql`). El frontend no las muestra: `/dashboard` tiene
StatsCards globales sin desglose por tenant, y `/dashboard/tenants/[slug]`
muestra info + módulos pero ningún usuario. Además no existe endpoint backend
que filtre usuarios/métricas por tenant.

Decisión del usuario: mostrar **las dos vistas** — ranking global en el
Overview + miembros en el detalle de cada tenant.

## Decisiones de diseño

- **Fuente de pertenencia**: `authharco.user_tenants` (N:M con rol por tenant),
  no el campo legacy `users.tenant_id`.
- **Endpoints nuevos** (en `endpoints/tenants.py`, orden: estáticos ANTES de
  `/{tenant_id}`; gated con `get_current_admin_user`):
  - `GET /tenants/usage` → ranking `[{slug, name, personas, admins,
    activas_30d, activos, ultimo_acceso}]`.
  - `GET /tenants/{tenant_id}/users` → miembros
    `[{id, username, email, role_tenant, status, login_count, last_login}]`.
- **Patrón backend**: DI chain repo → service → endpoint + schema Pydantic
  nuevo en `schemas/tenant.py` (estilo `UserStats`: repo devuelve dict,
  `response_model` tipa).
- **Frontend**: `ENDPOINTS.tenants.usage` y `ENDPOINTS.tenants.users(id)` en
  `api.config.ts`; card "Uso por tenants" en `dashboard/index.astro`;
  card "Miembros" en `dashboard/tenants/[slug].astro` (fetch al `Promise.all`
  existente). Tabla de ranking como componente `TenantUsageTable.svelte` con
  test vitest (test-first); la de miembros es HTML inline (precedente de las
  páginas).

## Tareas

- [x] **T1 — Backend endpoints + tests (test-first)**: RED (3 failed: 404/403) →
      implementar repo/service/schemas/endpoints → GREEN `14 passed`
      (5 tests nuevos + triangulación: tenant legacy no cuenta, tenant
      vacío, NULLS LAST, 403 non-admin, 404 unknown tenant).
      Endpoints: `GET /tenants/usage` → `TenantUsageResponse`;
      `GET /tenants/{id}/users` → `TenantMemberResponse`. Delegado a gentle-ai-worker.
- [x] **T2 — Frontend**: ENDPOINTS + `TenantUsageTable.svelte` (test
      vitest RED→GREEN, 5 tests) + card Overview + card Miembros en detalle
      (`.ok` guard → si el endpoint falla, la card no se muestra). Delegado.
- [x] **T3 — Verificación**: suite backend completa (gate cov 80) +
      vitest frontend + `npm run build`. Delegado a gentle-ai-verify.
      - Backend: **266 passed / 0 failed**, coverage **86.95%** (gate 80 ✅), ~19:51.
      - Frontend: **10 archivos / 112 tests passed** (vitest, sin coverage).
      - Build Astro: **0 errores** (solo warnings benignos de Node/vite).
      - Repo intacto: `git status` idéntico antes/después de la verificación.
- [x] **T4 — Commits work-unit** en rama `dev` (backend / frontend) +
      preflight de review nativo.
      - **Incidente**: el review del candidato completo (779 líneas / 13 archivos)
        expiró contra el bound del relay (15 min + 15 min/MB ≈ 15,76 min para
        53 KB) → stop `unachievable_lens_slot` en `review-06cc2f992caa7374`.
        Recuperación según los docs: dividir el candidato (regla de 400 líneas
        del skill RDD) y NO relanzar el slot idéntico.
      - **Slice frontend** (workspace, 289 líneas): `review-62a6d090d7b1ad1d` →
        approved + acknowledged (4 advisories R3-001..004 en páginas/componente).
      - **Slice backend** (rango commiteado baseRef `ba5bc30`): `review-bbdbfa57907b4381`
        → approved + acknowledged (2 advisories: test:456, TenantRepository:91).
        Se usó stash temporal para limpiar untracked elegibles y `baseRef`
        explícito (el default apuntaba a la tag v1.1.9 con 149 archivos).

## Evidencia / commits

- `2e6b203` `feat(tenants): add per-tenant usage ranking and member endpoints`
- `a0877a3` `feat(dashboard): show per-tenant usage ranking and tenant members`
- (pendiente: commit de esta doc)
