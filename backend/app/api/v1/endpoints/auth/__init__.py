"""
Endpoints de Autenticación
"""

from fastapi import APIRouter
from .login import router as login_router
from .google import router as google_router

router = APIRouter()
router.include_router(login_router, prefix="/auth", tags=["authentication"])
router.include_router(google_router, prefix="/auth", tags=["authentication"])
