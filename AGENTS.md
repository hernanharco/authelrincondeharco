# AGENTS.md — authCore

Coding standards for AI-assisted and human contributions.

## Backend (FastAPI + SQLAlchemy async + PostgreSQL)

- Python 3.12, type hints on all new functions; no untyped dicts at API boundaries (use Pydantic schemas).
- SQLAlchemy models live in `app/models/`, API routes in `app/api/v1/endpoints/`, business logic in `app/services/`.
- Tables live in the `authharco` schema — always schema-qualify in ad-hoc SQL.
- JWT is RS256; keys never leave the server; JWKS is the only public key surface.
- Migrations and seeds must be idempotent (`ON CONFLICT` / select-then-insert).
- Tests: pytest (`backend/tests/`), no network calls in tests. Run `cd backend && python -m pytest` (bare `pytest` breaks `sys.path`). Coverage gate `--cov-fail-under=80` is active in `backend/pyproject.toml` addopts.

## Frontend (Astro + Svelte 5)

- Server-rendered pages unless interaction requires client islands.
- Auth cookie: `access_token` (httpOnly), max-age = `ACCESS_TOKEN_EXPIRE_MINUTES` (default 120 min), `SameSite=Lax` dev / `SameSite=None` + `Secure` in production. Only the Google callback sets it; `POST /auth/login` returns the token in JSON and sets no cookie.

## General

- Conventional Commits (`feat:`, `fix:`, `chore:`).
- Do not commit secrets; `.env` files stay local.
- One feature or fix per branch/commit.
