# Feature: approval-tenant-membership — aprobar vincula al tenant de origen

Aprobación en AuthCore deja al usuario aprobado pero SIN membresía en `user_tenants`;
el tenant de origen (ej. riderdefensa) nunca queda relacionado. Resuelve la incidencia
reportada por el dueño y añade asignación manual como respaldo. Rama: `feat/approval-tenant-membership`.

## Specs

- **S1** — Al aprobar un usuario (`PATCH /users/{id}/status` → `ACTIVE`, y cualquier
  otro camino que active la cuenta: `bulk-update`, asignación de rol), si su campo
  `users.origin` coincide (case-insensitive) con el `slug` de un tenant activo,
  se crea automáticamente la membresía en `user_tenants` con rol `USER`, idempotente
  (nunca duplica una membresía existente).
  > "elianadeseguros lo aprobe pero no quedo relacionado con rider defensa que fue donde estaba pidiendo autorizacion"
- **S2** — Los usuarios ya aprobados sin membresía (ej. `elianadeseguros` →
  `riderdefensa`) se pueden vincular con un backfill idempotente; el backfill
  reporta los `origin` que no matchean ningún tenant para asignación manual.
- **S3** — El panel ofrece asignación manual usuario↔tenant (alta y baja de
  membresía con rol), como respaldo cuando `origin` no matchea `slug`
  (p. ej. origin `rincon` vs slug `rincom`, origins `google`/`dev-login`).
- **S4** — Auditoría de SUPERADMIN: solo la cuenta del dueño debe tenerlo.
  > "SUPERADMIN solo lo debe tener mi cuenta ningun otro usuario"
  Verifica: (a) en prod solo hay 1 SUPERADMIN y es la cuenta del dueño;
  (b) el código solo permite asignar SUPERADMIN/ADMIN desde SUPERADMIN
  (`UserDomain.can_assign_role`); (c) `dev-login` está bloqueado en producción.
- **S5** — Si `origin` no matchea ningún tenant, NO se crea membresía ni falla la
  aprobación: el usuario queda activo y pendiente de asignación manual (S3/S2).

## Tasks

- [ ] **T1** — S1, backend: hook de auto-asignación en `UserUpdateService`
      (update_user_status / update_user_role / bulk_update) + repositorio de
      membresías. Test-first RED→GREEN. Commit `feat(auth): auto-assign tenant membership on approval`.
- [ ] **T2** — S1, backend: cubrir también los caminos de activación no cubiertos
      si T1 no los cubre (bulk-update, role) con tests de regresión del comportamiento
      previo. Commit (o parte del commit de T1 si es unidad contigua).
- [ ] **T3** — S2, script de backfill idempotente + reporte de orígenes no matcheados.
      Commit `feat(scripts): idempotent membership backfill with unmatched report`.
- [ ] **T4** — S3, endpoints de alta/baja de membresía (admin) + tests.
      Commit `feat(api): manual user-tenant membership endpoints`.
- [ ] **T5** — S3, pantalla de asignación manual en el panel de AuthCore.
      Commit `feat(web): manual tenant membership assignment UI`.
- [ ] **T6** — S4, auditoría en prod (query) + constatación de guards; resultado
      en Log. Commit (docs/evidencia).
- [ ] **T7** — Cierre: suite completa, `gentle-ai-verify` (riesgo item 2),
      review nativo si `reviewDue`. Evidencia en Log.

## Log

- **L1** — petición original del usuario (verbatim): "elianadeseguros lo aprobe pero
  no quedo relacionado con rider defensa que fue donde estaba pidiendo autorizacion".
- **L2** — decisión del usuario: "sigamos con tu recomendacion y lo que dices SUPERADMIN
  solo lo debe tener mi cuenta ningun otro usuario".
- **L3** — decisiones de diseño acordadas: rol de membresía automática = `USER`
  (ascender a ADMIN a mano desde el panel si es dueño); sí a commits por tarea
  en rama feature, sin push.
- **L4** — hallazgo de exploración: la aprobación (`UserUpdateService.update_user_status`)
  solo cambia `status`/`is_active`; nada en el backend inserta en `user_tenants`
  (solo se lee desde `/users/me/tenants`, `/select-tenant`, `/tenants/usage`,
  `/tenants/{id}/users`). `origin` se deriva del host del `redirect_to`
  (google.py callback) y es solo una etiqueta, no una membresía.
