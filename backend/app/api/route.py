"""
API v1 Router.
Este módulo agrupa todos los routers de la versión 1 de la API.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, company, tenants, modules, tenant_modules, user_tenants

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(company.router, prefix="/company", tags=["company"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(modules.router, prefix="/modules", tags=["modules"])
api_router.include_router(tenant_modules.router, prefix="/tenant-modules", tags=["tenant-modules"])
api_router.include_router(user_tenants.router, prefix="/users", tags=["user-tenants"])
