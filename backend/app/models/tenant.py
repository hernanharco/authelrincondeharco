"""
Tenant model.
Define la estructura de la tabla tenants en la base de datos.
Un tenant es una organización/empresa que usa el SaaS.
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class Tenant(Base):
    """
    Modelo ORM de la tabla tenants.
    Responsabilidad única: representar la estructura de datos en la BD.
    """

    __tablename__ = "tenants"

    id = Column(
        String(36),
        primary_key=True,
        index=True,
        comment="UUID único del tenant",
    )

    slug = Column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Identificador corto (nanatamoda, rincom, etc.)",
    )

    name = Column(
        String(255),
        nullable=False,
        comment="Nombre visible de la empresa",
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si está activo puede usar el sistema",
    )

    website_url = Column(
        String(500),
        nullable=True,
        comment="URL del sitio web del tenant (ej: https://www.rincom.es)",
    )

    admin_url = Column(
        String(500),
        nullable=True,
        comment="URL del panel admin del tenant (ej: https://auth.rincom.es/dashboard)",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Fecha de creación del registro",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Última actualización del registro",
    )

    def __repr__(self) -> str:
        return f"<Tenant(slug='{self.slug}', name='{self.name}')>"
