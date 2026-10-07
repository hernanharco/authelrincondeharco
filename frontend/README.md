# AuthCore — Frontend (Astro + Svelte 5)

Dashboard de administración de authCore: páginas server-rendered con **Astro 6** e islas interactivas en **Svelte 5** (Runes), styling con **TailwindCSS 4** y tipado con **TypeScript 5**. El frontend consume el backend FastAPI (`backend/`) y protege las rutas del dashboard mediante un middleware que valida la cookie httpOnly `access_token` (JWT RS256).

## Comandos

| Comando | Acción |
| :------ | :----- |
| `pnpm install` | Instalar dependencias |
| `pnpm dev` | Dev server en `localhost:4321` |
| `pnpm build` | Build de producción |
| `pnpm preview` | Previsualizar el build |
| `pnpm test:run` | Tests vitest (una pasada; 107 tests / 9 suites) |
| `pnpm test` | Tests vitest en watch |
| `pnpm test:coverage` | Tests con cobertura (v8) |
| `pnpm astro ...` | CLI de Astro (`pnpm astro -- --help`) |

## Estructura de `src/`

```text
src/
├── components/
│   ├── auth/          # LoginForm, GoogleButton, PendingApproval, AuthAlert
│   ├── common/        # Icon
│   └── dashboard/     # UsersTable, StatsCard, RoleBadge, CompanyProfileForm, ...
├── config/
│   └── api.config.ts  # URLs de la API (BACKEND_URL, ENDPOINTS)
├── data/
│   └── countryCodes.ts
├── layouts/           # Layouts Astro
├── pages/             # Rutas Astro (index, login, logout, select-tenant,
│                      #   dashboard/, api/ endpoints server-side)
├── services/
│   └── authService.ts # Cliente HTTP de autenticación
├── styles/            # global.css (Tailwind)
├── utils/             # jwt.ts, guards.ts, auth.roles.ts, date.ts (lógica pura)
└── middleware.ts      # Auth de rutas: valida cookie access_token y rol
```

## Tests

Los tests viven en `frontend/tests/` (no dentro de `src/`), corren con **vitest** +
jsdom + @testing-library/svelte:

- `tests/middleware.test.ts`, `tests/pages/login.test.ts`
- `tests/services/authService.test.ts`
- `tests/auth/` (GoogleButton, LoginForm), `tests/dashboard/` (StatsCard, UsersTable)
- `tests/utils/` (jwt, guards)

```bash
pnpm test:run
```

## Variables de entorno

- `PUBLIC_BACKEND_URL`: URL del backend para el navegador (default `http://localhost:8000`).
- `API_TARGET`: URL del backend en SSR (dentro del contenedor Docker).
- El OAuth de Google se configura **en el backend** (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`
  en `backend/.env`); el frontend solo redirige a `GET /api/v1/auth/google`.
- `SITE_ORIGIN`: origen del sitio para el middleware (default `http://localhost:4321`).

## Flujo de sesión resumido

1. Login tradicional (`POST /api/v1/auth/login`) → token en JSON, sin cookie.
2. Google OAuth (`GET /api/v1/auth/google` → callback) → el backend setea la cookie
   httpOnly `access_token` (120 min) y redirige a `/dashboard` o `/select-tenant`.
3. `src/middleware.ts` exige cookie `access_token` válida (no expirada) y rol con
   acceso al dashboard en las rutas protegidas.
