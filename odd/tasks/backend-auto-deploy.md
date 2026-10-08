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

## Plan de deploy (modelo GHCR)

```
push a main (backend/** | compose.prod.yaml | el workflow)
  → Actions: build backend/Dockerfile → push ghcr.io/<repo>/backend:{sha,latest}
  → SSH a Hetzner: sync repo a origin/main → compose pull api → up -d --no-deps api
  → healthcheck /health dentro del contenedor
```

Postgres y Redis **no** se tocan (`--no-deps`).

## Tareas

- [x] **T1 — `compose.prod.yaml`: `image:` en el servicio api** — agregar
      `image: ghcr.io/hernanharco/authelrincondeharco/backend:latest` junto al
      `build:` existente (build queda como fallback local). Sin runner
      determinista local → verificación por validación de YAML + smoke test
      real (T4).
      Evidencia: línea `image:` agregada sobre `build:` en el servicio `api`;
      `yaml.safe_load` sin error.
- [x] **T2 — `.github/workflows/backend-deploy.yml`** — adaptado: Dockerfile
      (no `.prod`), healthcheck Python, `paths` con `backend/**`,
      `compose.prod.yaml` y el propio workflow; `workflow_dispatch`. El script
      SSH sincroniza el servidor a `origin/main` (fetch + checkout main +
      reset --hard, seguro porque `44882ac` ya está contenido en `main` vía
      el merge de T3) y luego pull + `up -d --no-deps api`.
      Evidencia: workflow creado con `file: ./backend/Dockerfile`, healthcheck
      `python`+`urllib`, sync SSH a `origin/main` y `paths` con el propio
      workflow; `yaml.safe_load` sin error; `grep -c 'Dockerfile.prod'` = 0 y
      `grep -c 'node -e'` = 0.
- [ ] **T3 — Traer a `main` el ajuste de compose del servidor** — merge
      `dev → main` para que el `compose.prod.yaml` trackeado incluya `44882ac`
      (el reset --hard del workflow no pierda ese cambio).
- [ ] **T4 — Secrets + smoke test** — `gh secret set` de `HETZNER_HOST`
      (Tailscale `100.111.99.61`, recomendado en la doc), `HETZNER_USER=root`,
      `HETZNER_SSH_KEY`; merge del PR (dispara el deploy por `paths`) y
      verificación: run de Actions verde + `git log` en el server + `/health`
      200 + endpoint `tenants/usage` sigue vivo.
- [ ] **T5 — Actualizar la doc de `core/`** — tabla de proyectos: authCore
      "❌ Falta Vercel" está desactualizado (hoy está conectado) y marcar el
      backend como auto-deploy. Nota: `core/` **no es repo git** (sin `.git`),
      así que es una edición de archivos locales.

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
