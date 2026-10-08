# Feature: user-tenants-table — desbloquear la tabla N:M usuario↔tenant

## Contexto

`authharco.user_tenants` no existe en la base dev. El `Base.metadata.create_all`
del startup falla en cada arranque con:

```
psycopg.errors.DatatypeMismatch: foreign key constraint "user_tenants_user_id_fkey"
cannot be implemented — Key columns "user_id" and "id" are of incompatible types:
character varying and integer.
```

Causa raíz: `users.id` es `Integer` (autoincrement) pero `UserTenant.user_id`
está declarado como `String(36)`. Los tests no lo detectan porque corren sobre
SQLite, que no valida tipos en FKs.

Impacto: `GET /users/me/tenants` y `POST /auth/select-tenant` fallarían para
usuarios no-SUPERADMIN (el SUPERADMIN hace bypass sin consultar la tabla).

## Tareas

- [x] **T1 — Fix del tipo FK + test** (test-first): test que valide que todo FK
      de `Base.metadata` apunta a una columna de tipo compatible (RED → fix
      `user_tenant.py`: `user_id` → `Integer` → GREEN).
      - RED: `user_tenants.user_id (string) -> users.id (integer)` (1 failed, 14 passed)
      - GREEN: `15 passed` — `backend/tests/test_models.py::TestIntegridadForeignKeys`
      - Ejecutado con `backend/.venv/bin/python -m pytest` (pytest solo vive en el venv)
- [x] **T2 — Verificar en la base dev**: restart del backend, confirmar que
      `authharco.user_tenants` se crea, y probe HTTP de `GET /users/me/tenants`.
      - Tabla creada: `user_id integer`, FKs `user_tenants_user_id_fkey` + `user_tenants_tenant_id_fkey` + `uq_user_tenant` presentes.
      - Hallazgo extra: drift en `tenants` (faltaban `website_url`/`admin_url`) → `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` idempotente aplicado en dev.
      - Probe: `POST /auth/dev-login` → token, `GET /users/me/tenants` → HTTP 200 con tenant `rincom`.
      - Path NO superadmin (la query real sobre `user_tenants`) verificado en psql con semilla idempotente `dev_admin ↔ rincom`.
- [x] **T3 — Guardar `scripts/tenant-usage.sql`**: queries de uso por tenant
      (resumen, detalle, huérfanos, ranking) ya probadas contra la base.
      - Las 4 queries ejecutadas desde el archivo con `docker exec -i ... psql < scripts/tenant-usage.sql` → resultados OK.

## Evidencia / commits

- **Suite completa**: `261 passed` / `0 failed` / coverage **86.71%** (gate 80) — vía `gentle-ai-verify`, log en `/tmp/pytest_full.log`.
- **Review nativo**: lineage `review-aa28bd1bb1cc73ad`, tier medium, lente `review-reliability` → **approved** y acknowledged (autoridad quemada, `gentle-ai.review-acknowledged/v1`).
- **Findings advisories (no bloqueantes, futuro trabajo)**:
  - R3-001 `backend/app/models/user_tenant.py:29` (SUGGESTION)
  - R3-002 `backend/tests/test_models.py:253` (SUGGESTION)
  - R3-003 `scripts/tenant-usage.sql:23` (SUGGESTION)
  - R3-004 `.atl/.skill-registry.cache.json:3` (SUGGESTION)
- **Commits**: pendiente de decisión del usuario (sin commit aún en rama `dev`).
