# Feature: fix-tenant-members-expand — the tenant usage row expander does nothing in prod

## Context

The "Uso por tenants" card on `/dashboard` shows a chevron per tenant that should expand
an inline list of that tenant's members. In production (https://auth.rincom.es/dashboard)
pressing it does absolutely nothing. The 12 vitest cases in
`frontend/tests/dashboard/TenantUsageTable.test.ts` pass, so the component logic is sound.

Root causes, established with evidence (not assumed):

1. **The component is never hydrated.** `frontend/src/pages/dashboard/index.astro:203`
   renders `<TenantUsageTable usage={tenantUsage} />` with no `client:*` directive, so
   Astro renders it server-side only. The button exists in the HTML with no listener.
   Proof: every other interactive component in the repo carries the directive
   (`Icon`, `OriginChart`, `LoginForm`, `RoleBadge`, ...), and the string
   "No se pudieron cargar los miembros" / "by-slug" does not appear in any
   `frontend/dist/client/_astro/*.js` chunk. A Chrome hit-test on the real markup +
   compiled CSS confirmed the click lands on the `<button>` (the stretched-link
   `::after` is 91x19px, button is `z-20` over the link's `z-10`), so hit-testing is ruled out.
2. **Token acquisition is broken for a cross-origin frontend.** `TenantUsageTable.svelte:59`
   reads `document.cookie`, but the backend sets `access_token` **httpOnly**
   (`backend/app/api/v1/endpoints/auth/login.py:63-71`, `auth/google.py:115-149`).

Verified topology (curl against live infra):

- Frontend: Vercel at `auth.rincom.es` (`server: Vercel`). No same-origin API proxy:
  `https://auth.rincom.es/api/v1/...` returns a Vercel 404.
- Backend: only reachable at `api-authcore.elrincondeharco.com` (Cloudflare).
  `api.rincom.es` is NOT the backend (`/openapi.json` -> 404 there, 200 on the real host).
- CORS on the backend is already correct for `https://auth.rincom.es`
  (`allow-origin`, `allow-credentials: true`, `allow-headers: authorization`).

**Decision (user, 2026-10-09):** because the two hosts are different registrable sites,
no cookie `Domain` can serve both: `Domain=.rincom.es` never travels to the backend, and a
host-only cookie would disappear from `auth.rincom.es` and break the Vercel middleware
session. So the fix is the SSR-token pattern already used by the repo
(`data-token={token}` in `layouts/DashboardLayout.astro:172`, consumed by
`dashboard/pending/index.astro:119` and `dashboard/users/[id].astro:217`), **not** a
backend `Domain` change and **not** a fetch migrated to `credentials: 'include'` alone.

Explicitly rejected for now (documented so it is not "fixed" again later):
changing `cookie_domain` in the backend, and relying on `credentials: 'include'`
while the session cookie is scoped to `.rincom.es`.

## Scope

- `frontend/src/pages/dashboard/index.astro` — hydrate the component and pass the SSR token.
- `frontend/src/components/dashboard/TenantUsageTable.svelte` — accept `token` as a prop,
  drop `getAuthToken()`/`document.cookie`.
- `frontend/tests/dashboard/TenantUsageTable.test.ts` — new contract (prop `token`).
- `frontend/src/pages/dashboard/tenants/[slug]/manage.astro` (2 fetches) and
  `frontend/src/pages/select-tenant/index.astro` (1 fetch) — same `document.cookie`
  defect, already authorized by the user.

Not in scope: the Vercel `/api/*` same-origin rewrite (hygiene follow-up), and any
backend change.

## Tasks

- [x] **T1 — Component + tests (test-first)**: contract moved to a `token` prop,
      `getAuthToken()`/`document.cookie` deleted, `Authorization` asserted on both
      fetches. **RED** (1 failed / 118 passed) before the component change:
      `expected { Authorization: 'Bearer null' } to match { Authorization: 'Bearer test-token-123' }`
      — the component still read the now-unseeded cookie. **GREEN** (119 passed) after.
      Route: delegated (`gentle-ai-worker`), trigger: multi-file write rule.
- [x] **T2 — Hydration**: `<TenantUsageTable usage={tenantUsage} token={token} client:load />`
      in `dashboard/index.astro:203`. Route: delegated (same writer run as T1).
- [x] **T3 — Same defect in `manage.astro`** (2 reads) **and `select-tenant/index.astro`**
      (1 read): all three now take the SSR token from a `data-token` container attribute,
      matching `dashboard/pending` and `dashboard/users/[id]`. Route: delegated (same run).
- [x] **T4 — Verification**: frontend vitest **10 files / 119 tests passed, 0 failed**;
      `npm run build` exit 0, "Build Complete!", 0 errors (only the pre-existing Node
      `module.register()` deprecation warning); structural hydration proof: `grep -rl
      "No se pudieron cargar los miembros" frontend/dist/client/_astro/*.js` went from
      **exit 1 (no match)** to **`TenantUsageTable.bVoG8vfz.js`**.
      Parent spot check: re-ran vitest (119/119) and the bundle grep independently.
- [x] **T5 — Work-unit commits** on `fix/tenant-members-expand`, with the parent
      re-running its own spot check first. Native review preflight via `assess`
      (`baseRef 38a5237`, `committedOnly: true`): **risk medium** (reason
      `executable_change` on `TenantUsageTable.svelte`), **`reviewDue: false` —
      `under_budget`**, writer profile `large`, `rddLine: on`,
      `nativeReviewOutcome: unknown`. Plan returned: `writerSelfVerification: true`,
      `independentVerifier: false` — the writer's report plus the parent spot check is
      the verification of record for this candidate; native review defers to the PR slice.

## Evidence / commits

- `89554bd` `fix(dashboard): hydrate tenant usage table and pass token from SSR`
  (component + island + tests)
- `5c09603` `fix(dashboard): replace unreadable cookie reads with SSR data-token`
  (manage.astro + select-tenant)

Total: 86 changed lines (49 insertions / 46 deletions across 5 source files), well under
the 400-line advisory; single PR.

Incident: the local `.git/hooks/pre-commit` hook (`gga run`, `PROVIDER: claude`,
`STRICT_MODE: true`) failed with `Not logged in - Please run /login`, aborting every
commit. The user explicitly authorized `--no-verify` for these commits after reviewing
that the hook only matched a `*.test.ts` file in this scope. Hook and global gga config
were left untouched.

## Open follow-up (out of scope, needs a user decision)

- `select-tenant/index.astro:134` still **writes** `document.cookie = access_token=...`
  after a successful selection. Writing cannot override an httpOnly cookie, so the rotated
  token may never reach `auth.rincom.es`; pre-existing behaviour, unchanged here.
- The Vercel `/api/*` same-origin rewrite (would remove the need to expose the JWT in
  page HTML at all) remains the recommended hygiene fix for the cross-origin login design.

## Checks

- `cd frontend && npx vitest run` — **10 files / 119 tests, 0 failed** (run by the writer
  after all page edits, then re-run independently by the parent).
- `cd frontend && npm run build` — exit 0, "Build Complete!", 0 errors.
- Structural proof of hydration: `grep -rl "No se pudieron cargar los miembros" frontend/dist/client/_astro/*.js`
  matched nothing before, matches `TenantUsageTable.bVoG8vfz.js` after.

**Pending / not run**: no dev-server or production smoke test was executed against the
live backend, so the SSR island serialization is proven at build level only. Verify by
hand after deploy: open `/dashboard`, expand a tenant row, confirm the members render.

## Forecast / delivery

Authored changed lines forecast: ~70 (well under the 400-line advisory), single PR.
