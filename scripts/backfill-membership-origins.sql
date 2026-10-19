-- backfill-membership-origins.sql — approval-tenant-membership (S2)
--
-- Vincula en authharco.user_tenants a los usuarios YA aprobados (ACTIVE)
-- que no tienen ninguna membresía, usando el mismo criterio que el backend
-- (MembershipService.assign_by_origin): users.origin == tenants.slug,
-- case-insensitive, tenant activo, rol 'USER'.
--
-- Idempotente: NOT EXISTS por par (user, tenant) + ON CONFLICT no aplica
-- porque solo inserta filas que faltan (AGENTS.md: seeds idempotentes).
--
-- Uso:
--   docker exec -i authcore-dev-db psql -U authcore -d authcore < scripts/backfill-membership-origins.sql
--   (en prod: psql "$DATABASE_URL" -f scripts/backfill-membership-origins.sql)
--
-- Secciones:
--   1. PREVIEW (solo lectura): qué se insertaría — revisar antes.
--   2. INSERT idempotente.
--   3. POST: resultado por tenant.
--   4. POST: origins sin tenant matcheado → asignación manual (S3/S5).

-- ── 1. PREVIEW: candidatos a backfill (solo lectura) ──────────────────────
SELECT u.id          AS user_id,
       u.username,
       u.email,
       u.origin,
       t.slug        AS tenant_slug
FROM authharco.users u
JOIN authharco.tenants t
  ON lower(t.slug) = lower(u.origin)
 AND t.is_active
WHERE u.status = 'ACTIVE'
  AND NOT EXISTS (
        SELECT 1 FROM authharco.user_tenants ut
        WHERE ut.user_id = u.id
          AND ut.tenant_id = t.id
      )
ORDER BY t.slug, u.username;

-- ── 2. INSERT idempotente ─────────────────────────────────────────────────
INSERT INTO authharco.user_tenants (id, user_id, tenant_id, role, created_at)
SELECT gen_random_uuid()::text,
       u.id,
       t.id,
       'USER',
       now()
FROM authharco.users u
JOIN authharco.tenants t
  ON lower(t.slug) = lower(u.origin)
 AND t.is_active
WHERE u.status = 'ACTIVE'
  AND NOT EXISTS (
        SELECT 1 FROM authharco.user_tenants ut
        WHERE ut.user_id = u.id
          AND ut.tenant_id = t.id
      );

-- ── 3. POST: membresías por tenant (quién quedó vinculado) ────────────────
SELECT t.slug                              AS tenant,
       count(ut.user_id)                   AS personas,
       count(ut.user_id) FILTER (WHERE ut.role = 'ADMIN') AS admins
FROM authharco.tenants t
LEFT JOIN authharco.user_tenants ut ON ut.tenant_id = t.id
GROUP BY t.slug
ORDER BY personas DESC, t.slug;

-- ── 4. POST: usuarios ACTIVE sin membresía y su origin NO matchea ningún
--        tenant → pendientes de asignación manual desde el panel (S3) ──────
SELECT u.username,
       u.email,
       u.origin,
       u.created_at
FROM authharco.users u
WHERE u.status = 'ACTIVE'
  AND NOT EXISTS (
        SELECT 1 FROM authharco.user_tenants ut WHERE ut.user_id = u.id
      )
  AND (
        u.origin IS NULL
     OR NOT EXISTS (
          SELECT 1 FROM authharco.tenants t
          WHERE lower(t.slug) = lower(u.origin) AND t.is_active
        )
      )
ORDER BY u.created_at;
