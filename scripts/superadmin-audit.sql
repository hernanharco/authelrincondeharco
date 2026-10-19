-- superadmin-audit.sql — approval-tenant-membership (S4)
--
-- "SUPERADMIN solo lo debe tener mi cuenta ningun otro usuario"
--
-- Re-auditoría idempotente (solo lectura): quién tiene rol SUPERADMIN.
-- Esperado en prod: EXACTAMENTE 1 fila (la cuenta del dueño).
-- En dev es esperable 2: el dueño + dev_admin (creado por /auth/dev-login,
-- que responde 403 en producción — cubierto por
-- tests/test_dev_login_endpoints.py::test_dev_login_disabled_in_production).
--
-- Uso:
--   docker exec -i authcore-dev-db psql -U authcore -d authcore < scripts/superadmin-audit.sql
--   (en prod: psql "$DATABASE_URL" -f scripts/superadmin-audit.sql)

SELECT u.id,
       u.username,
       u.email,
       u.status,
       u.origin,
       u.created_at,
       u.last_login
FROM authharco.users u
WHERE u.role = 'SUPERADMIN'
ORDER BY u.created_at;
