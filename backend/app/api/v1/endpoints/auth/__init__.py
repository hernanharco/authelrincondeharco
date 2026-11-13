"""
Endpoints de Autenticación
"""

from fastapi import APIRouter

from .data_token import router as data_token_router
from .dev_login import router as dev_login_router
from .google import router as google_router
from .login import router as login_router
from .sessions import router as sessions_router

router = APIRouter()
router.include_router(login_router)
router.include_router(google_router)
router.include_router(dev_login_router)
router.include_router(data_token_router)
router.include_router(sessions_router)
