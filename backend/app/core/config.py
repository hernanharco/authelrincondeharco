import json
from typing import Any, List, Optional
from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración inteligente y agnóstica para authCore.
    Maneja la construcción de DB URL, Google OAuth y parseo robusto de CORS.
    """

    # --- Dominio de la aplicación ---
    APP_DOMAIN: str = Field("", alias="APP_DOMAIN")

    # --- Logging ---
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # Titulo del proyecto
    TITLE_BACKEND: str = Field("authCore-Backend", alias="TITLE_BACKEND")

    # --- Configuración de Pydantic ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Permite que las variables funcionen en Mayus/Minus
        extra="ignore",  # Ignora variables sobrantes en el .env
    )

    # --- Identificación del Backend ---
    title_backend: str = Field("authCore-Backend", alias="TITLE_BACKEND")

    # --- Entorno y Debug ---
    ENVIRONMENT: str = "development"
    DEBUG: bool = Field(False, alias="DEBUG")
    SECRET_KEY: str = Field(..., alias="SECRET_KEY")

    # --- Base de Datos (Variables individuales) ---
    pg_host: str = Field(..., alias="PGHOST")
    pg_port: int = Field(5432, alias="PGPORT")
    pg_database: str = Field(..., alias="PGDATABASE")
    pg_user: str = Field(..., alias="PGUSER")
    pg_password: str = Field(..., alias="PGPASSWORD")
    pg_schema: str = Field("public", alias="PGSCHEMA")
    pg_sslmode: str = Field("disable", alias="PGSSLMODE")
    pg_channel_binding: str = Field("disable", alias="PGCHANNELBINDING")

    @computed_field
    @property
    def database_url(self) -> str:
        """
        Construye la URL de conexión asíncrona para SQLAlchemy + Psycopg3.
        Aplica aislamiento de Schema mediante search_path.
        """
        return (
            f"postgresql+psycopg://{self.pg_user}:{self.pg_password}@"
            f"{self.pg_host}:{self.pg_port}/{self.pg_database}?"
            f"options=-csearch_path%3D{self.pg_schema}&"
            f"sslmode={self.pg_sslmode}"
        )

    # --- JWT Settings ---
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field("RS256", alias="ALGORITHM")
    API_V1_STR: str = "/api/v1"

    # --- Claves RSA para RS256 ---
    # Si no se proveen, se auto-generan en app/core/crypto.py
    rsa_private_key: Optional[str] = Field(None, alias="RSA_PRIVATE_KEY")
    rsa_public_key: Optional[str] = Field(None, alias="RSA_PUBLIC_KEY")

    # --- Google OAuth ---
    google_client_id: str = Field("", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field("", alias="GOOGLE_CLIENT_SECRET")

    # --- CORS Configuration (Lógica Robusta) ---
    # Usamos Any para evitar que Pydantic intente parsear el JSON antes de tiempo
    cors_origins: Any = Field(default_factory=list, alias="CORS_ORIGINS")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """
        Parsea dinámicamente: ["url1", "url2"], "url1, url2" o "*"
        """
        if not v:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        if isinstance(v, str):
            v = v.strip()
            # Si es formato JSON como tu .env: ["url", "url"]
            if v.startswith("[") and v.endswith("]"):
                try:
                    data = json.loads(v)
                    if isinstance(data, list):
                        return [str(i).strip() for i in data]
                except (json.JSONDecodeError, TypeError):
                    v = v.strip("[]")
            # Si es formato separado por comas o fallback
            return [i.strip().strip('"').strip("'") for i in v.split(",") if i.strip()]
        return []

    # --- URLs de Frontend y Backend ---
    frontend_origin: Optional[str] = Field(None, alias="FRONTEND_ORIGIN")
    backend_url: str = Field("http://localhost:8000", alias="BACKEND_URL")

    # --- Cloudinary (Opcionales por si los usas luego) ---
    cloudinary_cloud_name: Optional[str] = Field(None, alias="CLOUDINARY_CLOUD_NAME")
    cloudinary_api_key: Optional[str] = Field(None, alias="CLOUDINARY_API_KEY")
    cloudinary_api_secret: Optional[str] = Field(None, alias="CLOUDINARY_API_SECRET")

    # --- Helpers ---
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


# Instancia global única
settings = Settings()
