# Feature: backend-auto-deploy — CI/CD del backend a Hetzner (patrón GHCR)

## Contexto

El deploy del backend es **manual**: `scripts/deploy.sh` hace SSH a Hetzner,
`git pull` y `docker compose up -d --build`. El 2026-10-08 un merge a `main`
actualizó el frontend (Vercel) pero no el backend → la feature tenant-usage-ui
fue invisible en producción hasta redesplegar a mano (obs. Engram 2150).

El ecosistema ya tiene el patrón resuelto y documentado en
`~/Documentos/elrincondeharco.com/core/deploy/GITHUB-ACTIONS-HETZNER.md`
(vidasaludable, radar, portfolio). authCore quedó como excepción.

Decisión del usuario: **patrón GHCR** (idéntico al del ecosistema) e
**implementar ahora** (no solo abrir un issue).

## Diferencias con el template documentado (por eso no se copia tal cual)

1. **Dockerfile**: el template asume `backend/Dockerfile.prod`; authCore tiene
   `backend/Dockerfile`.
2. **Healthcheck**: el template usa `node -e "fetch(...)"`; el contenedor `api`
   es Python 3.12 (sin node) → usar `urllib`.
3. **Compose en el servidor**: el template asume que `/opt/authcore` ya tiene
   el `compose.prod.yaml` con `image:`. El servidor está desactualizado y en la
   rama `dev` con un commit local (`44882ac`, ajuste de compose hecho en prod,
   ya mergeado en `dev` vía `4178b7c`) → el workflow debe sincronizar el repo a
   `origin/main` antes del pull de imagen.
4. **Repo público** ⇒ la imagen GHCR será pública y el servidor hará pull sin
   PAT. Si el repo pasara a privado, haría falta un PAT con `read:packages` en
   el servidor (condición futura, no parte de este cambio).

**Hallazgo (webhook, no SSH):** el patrón SSH del template
(`core/deploy/GITHUB-ACTIONS-HETZNER.md`) es inaplicable a authCore: el puerto
22 de Hetzner solo acepta WireGuard (10.0.0.0/24) y Tailscale (100.64.0.0/10)
— verificado con `ufw status` — y los runners hosted de GitHub no están en esas
redes. Lo confirma el comentario en el workflow de vidasaludable: el job SSH
viejo fallaba con `dial tcp :22: i/o timeout` en cada run. El mecanismo real de
deploy es `deploy-webhook.service` en el servidor (push de GitHub →
`git reset --hard origin/main` → `docker compose up -d --build` en
`/opt/<repo>`). Decisión del usuario: webhook para el deploy y el job de
Actions queda **solo como verificación de build** (build + push GHCR).

## Plan de deploy (modelo GHCR)

```
push a main (backend/** | compose.prod.yaml | el workflow)
  → deploy-webhook.service en el servidor (el único camino que alcanza Hetzner):
    cd /opt/<repo> → git reset --hard origin/main
    → docker compose up -d --build (el build ocurre en el servidor)
  → Actions (Build Backend): solo verifica que backend/Dockerfile buildea
    (build + push ghcr.io/<repo>/backend:{sha,latest}; el runtime NO consume GHCR)
```

Postgres y Redis **no** se ven afectados (`up -d --build` solo recrea los
servicios cuyo código/imagen cambió).

## Tareas

- [x] **T1 — `compose.prod.yaml`: `image:` en el servicio api** — agregar
      `image: ghcr.io/hernanharco/authelrincondeharco/backend:latest` junto al
      `build:` existente (build queda como fallback local). Sin runner
      determinista local → verificación por validación de YAML + smoke test
      real (T4).
      Evidencia: línea `image:` agregada sobre `build:` en el servicio `api`;
      `yaml.safe_load` sin error.
- [x] **T2 — `.github/workflows/backend-deploy.yml`** — **solo build+push a
      GHCR** (verificación de que `backend/Dockerfile` buildea; nombre
      `Build Backend`, `outputs.image_tag`, `paths` con `backend/**`,
      `compose.prod.yaml` y el propio workflow, `workflow_dispatch`). **Sin job
      SSH**: el puerto 22 de Hetzner está restringido a WireGuard/Tailscale y
      los runners hosted no lo alcanzan (ver hallazgo arriba); el deploy real
      lo hace el webhook del servidor (T6).
      Evidencia: workflow sin job `deploy`, sin secrets `HETZNER_*` ni
      `appleboy/ssh-action`; `yaml.safe_load` sin error; `grep -c 'HETZNER'` = 0.
- [x] **T3 — Traer a `main` el ajuste de compose del servidor** — hecho vía
      cherry-pick `44882ac` → `af6bc07` en esta rama (el `reset --hard` del
      webhook no pierde el healthcheck de PG a 30s ni la red externa).
- [x] **T4 — Smoke test** — ✅ 2026-10-08 (merge PR #16). Sin secrets `HETZNER_*`
      (el SSH fue eliminado del workflow; ninguna credencial nueva en GitHub).
      Resultado: log del webhook `Push to main` → `Deploying` → server en
      `b4cc86f` (= `origin/main`); `api` y `web` recreados, `postgres`/`redis`
      intactos; `/health` **200**; `tenants/usage` y `tenants/{id}/users`
      **401** (vivos, piden auth) vía `api-authcore.` + dominio del ecosistema;
      red externa conservada; healthcheck de PG en **30s**; Actions
      "Build Backend" **completed/success** (GHCR).
- [x] **T5 — Actualizar la doc de `core/`** — hecho (nota: `core/` **no es repo
      git**, fue edición local). `GITHUB-ACTIONS-HETZNER.md`: cabecera «⚠️
      Corrección importante: el job SSH no funciona» con la evidencia (ufw +
      comentario de vidasaludable) y fila authCore corregida a `✅ Vercel`.
      `DEPLOY-PIPELINE.md`: fecha, diagrama, bloque «⚠️ el deploy real NO lo
      hace Actions» con el flujo webhook paso a paso, fila authCore
      `Vercel ✅ | Hetzner :8000 | ✅ (webhook) | Activo`, y 2 typos del nombre
      del repo corregidos.
- [x] **T6 — Webhook de deploy para authCore** —
      (a) ✅ symlink `/opt/authelrincondeharco → /opt/authcore` creado y
      verificado (`git -C` resuelve al repo);
      (b) ✅ webhook registrado en GitHub `id 694334756` →
      `https://webhook.rincom.es/webhook`, content-type `json`, eventos `push`,
      secret = `WEBHOOK_SECRET` (64 hex) del `/opt/deploy-webhook/.env`;
      (c) ✅ smoke test: push a `main` (merge PR #16) → deploy ejecutado y
      verificado (ver T4).
      Verificación de conectividad ya hecha: ping de GitHub recibido con firma
      HMAC válida (log `Ignored: ... from authelrincondeharco`, no
      `Invalid signature`) y el push de la rama descartado correctamente por no
      ser `refs/heads/main`.
      Pre-flight del deploy: red externa `elrincondeharco_net` existe y el api
      ya está conectado a ella + `authcore_default`; `compose config --quiet`
      OK en el server.

## Criterios de aceptación

- Un push a `main` que toque `backend/**` o `compose.prod.yaml` despliega el
  backend sin intervención manual.
- `workflow_dispatch` permite redesplegar a demanda.
- Postgres/Redis intactos durante el deploy; downtime del api acotado al
  recreado del contenedor (segundos).
- La doc de `core/` refleja el estado real.

## Riesgos / notas

- El `reset --hard origin/main` en el servidor descarta trabajo local no
  trackeado (el `.bak` sin trackear `compose.prod.yaml.bak-20261005` persiste;
  no se commitea nunca).
- El `.env` del servidor (secretos de DB/OAuth) vive en `/opt/authcore/.env`,
  gitignored: no lo toca el workflow.
- `scripts/deploy.sh` queda obsoleto tras esto; decidir si se elimina en este
  cambio o se documenta como legacy (fuera del alcance mínimo).
