"""
TenantModule model.
Tabla intermedia entre Tenant y Module.
Aquí viven los feature flags: is_active + settings JSONB.
"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class TenantModule(Base):
    """
    Modelo ORM de la tabla tenant_modules.
    Responsabilidad única: representar qué módulos tiene cada tenant
    y con qué configuración.
    """

    __tablename__ = "tenant_modules"

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK al tenant",
    )

    module_id = Column(
        String(50),
        ForeignKey("modules.id", ondelete="CASCADE"),
        primary_key=True,
        comment="FK al módulo",
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Feature flag: True = módulo habilitado para este tenant",
    )

    settings = Column(
        JSON,
        nullable=True,
        comment="Configuración específica del módulo para este tenant (providers, etc.)",
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

    # Relaciones ORM
    tenant = relationship("Tenant", backref="tenant_modules")
    module = relationship("Module", backref="tenant_modules")

    def __repr__(self) -> str:
        return f"<TenantModule(tenant='{self.tenant_id}', module='{self.module_id}', active={self.is_active})>"
