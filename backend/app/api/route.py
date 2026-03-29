"""
API v1 Router.
Este módulo agrupa todos los routers de la versión 1 de la API.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
