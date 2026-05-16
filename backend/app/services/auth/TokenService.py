"""
Servicio de Tokens JWT - Principio de Responsabilidad Única
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from jose import JWTError, jwt
from app.core.config import settings
from app.interfaces.auth.ITokenService import ITokenService


class TokenService(ITokenService):
    """
    Implementación concreta del servicio de tokens JWT.
    Maneja solo la creación, validación y revocación de tokens.
    """
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        # En producción, usar Redis o base de datos para blacklist
        self._blacklisted_tokens: set = set()
    
    async def create_access_token(self, data: Dict[str, Any], 
                                expires_delta: Optional[int] = None) -> Tuple[str, datetime]:
        """
        Crea un token de acceso JWT.
        """
        to_encode = data.copy()
        
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + timedelta(seconds=expires_delta)
        else:
            expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt, expire
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verifica y decodifica un token JWT.
        """
        try:
            # Verificar si está en blacklist
            if await self.is_token_revoked(token):
                return None
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    async def refresh_token(self, refresh_token: str) -> Optional[Tuple[str, datetime]]:
        """
        Refresca un token de acceso usando un refresh token.
        """
        payload = await self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # Revocar el refresh token anterior
        await self.revoke_token(refresh_token)
        
        # Crear nuevo access token
        user_data = {"sub": payload.get("sub"), "type": "access"}
        return await self.create_access_token(user_data)
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoca un token (añade a blacklist).
        """
        try:
            self._blacklisted_tokens.add(token)
            return True
        except Exception:
            return False
    
    async def is_token_revoked(self, token: str) -> bool:
        """
        Verifica si un token está revocado.
        """
        return token in self._blacklisted_tokens
    
    def get_token_payload(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el payload de un token sin verificar expiración.
        Útil para debugging.
        """
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
        except JWTError:
            return None
