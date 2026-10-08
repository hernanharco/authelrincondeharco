-- tenant-usage.sql — Métricas de uso por tenant (authCore)
--
-- Uso:
--   docker exec -i authcore-dev-db psql -U authcore -d authcore < scripts/tenant-usage.sql
--   (en prod: psql "$DATABASE_URL" -f scripts/tenant-usage.sql)
--
-- Fuente de verdad de pertenencia: authharco.user_tenants (N:M, con rol por tenant).
-- El campo legacy users.tenant_id queda excluido a propósito.
-- Todas las queries son de solo lectura e idempotentes.

-- ── 1. Resumen por tenant: cuántas personas, cuántas activas ─────────────
SELECT t.slug,
       t.name,
       count(ut.user_id)                                                  AS personas,
       count(ut.user_id) FILTER (WHERE ut.role = 'ADMIN')                 AS admins,
       count(ut.user_id) FILTER (WHERE u.last_login > now() - interval '30 days') AS activas_30d,
       count(ut.user_id) FILTER (WHERE u.status = 'ACTIVE')               AS estado_active,
       max(u.last_login)                                                  AS ultimo_acceso
FROM authharco.tenants t
LEFT JOIN authharco.user_tenants ut ON ut.tenant_id = t.id
LEFT JOIN authharco.users u         ON u.id = ut.user_id
GROUP BY t.slug, t.name
ORDER BY personas DESC;

-- ── 2. Quiénes son: detalle de usuarios por tenant ───────────────────────
SELECT t.slug,
       u.username,
       u.email,
       ut.role,
       u.status,
       u.login_count,
       u.last_login
FROM authharco.user_tenants ut
JOIN authharco.tenants t ON t.id = ut.tenant_id
JOIN authharco.users   u ON u.id = ut.user_id
ORDER BY t.slug, u.last_login DESC NULLS LAST;

-- ── 3. Huérfanos: usuarios sin ningún tenant ─────────────────────────────
SELECT u.username, u.email, u.status, u.created_at
FROM authharco.users u
LEFT JOIN authharco.user_tenants ut ON ut.user_id = u.id
WHERE ut.user_id IS NULL
ORDER BY u.created_at;

-- ── 4. Ranking de uso: usuarios más activos (global) ─────────────────────
SELECT u.username,
       t.slug                              AS tenant,
       u.login_count,
       u.last_login
FROM authharco.users u
LEFT JOIN authharco.user_tenants ut ON ut.user_id = u.id
LEFT JOIN authharco.tenants t        ON t.id = ut.tenant_id
ORDER BY u.login_count DESC, u.last_login DESC NULLS LAST;
