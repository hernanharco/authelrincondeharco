"""
Servicio de Google OAuth - Principio de Responsabilidad Única
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
import requests
from app.core.config import settings
from app.models.user import User
from app.interfaces.auth.IOAuthService import IOAuthService


class GoogleOAuthService(IOAuthService):
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Intercambia un authorization code por tokens y devuelve info del usuario.
        Authorization Code Flow.
        """
        try:
            # Paso 1: intercambiar code por access_token
            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
            response = requests.post(token_url, data=data)
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al intercambiar código con Google: {response.text}",
                )

            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se recibió access_token de Google",
                )

            # Paso 2: obtener info del usuario con el access_token
            userinfo_response = requests.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al obtener información del usuario de Google",
                )

            return userinfo_response.json()

        except HTTPException:
            raise
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo contactar con los servidores de Google",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en Google OAuth: {str(e)}",
            )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verifica un access_token llamando a la API de userinfo de Google.
        """
        try:
            response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token de Google inválido o expirado"
                )
            
            return response.json()
            
        except HTTPException:
            raise
        except requests.exceptions.ConnectionError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No se pudo contactar con los servidores de Google"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error en autenticación: {str(e)}"
            )

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del usuario desde Google.
        """
        try:
            user_info = await self.verify_token(token)
            return {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "given_name": user_info.get("given_name"),
                "family_name": user_info.get("family_name"),
                "locale": user_info.get("locale"),
                "verified_email": user_info.get("email_verified", False)
            }
        except Exception:
            return None
    
    async def create_user_from_oauth(self, user_info: Dict[str, Any]) -> Optional[User]:
        return None
    
    def get_provider_name(self) -> str:
        return "google"