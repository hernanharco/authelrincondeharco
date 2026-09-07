"""
Endpoints de Autenticación
"""

from fastapi import APIRouter
from .login import router as login_router
from .google import router as google_router
from .dev_login import router as dev_login_router

router = APIRouter()
router.include_router(login_router)
router.include_router(google_router)
router.include_router(dev_login_router)
