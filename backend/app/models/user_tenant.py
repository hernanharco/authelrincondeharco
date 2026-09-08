"""
UserTenant model.
Tabla intermedia N:M entre Users y Tenants.
Un usuario puede pertenecer a múltiples tenants con diferentes roles.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class UserTenant(Base):
    """
    Relación usuario ↔ tenant.
    Cada fila dice: "este usuario pertenece a este tenant con este rol".
    """

    __tablename__ = "user_tenants"

    id = Column(
        String(36),
        primary_key=True,
        comment="UUID único de la asignación",
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK al usuario",
    )

    tenant_id = Column(
        String(36),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="FK al tenant",
    )

    role = Column(
        String(20),
        nullable=False,
        default="USER",
        comment="Rol del usuario EN ESTE tenant (ADMIN, MANAGER, USER, VIEWER)",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Fecha de creación",
    )

    # Relaciones
    user = relationship("User", backref="user_tenants")
    tenant = relationship("Tenant", backref="user_tenants")

    # Un usuario no puede tener dos registros para el mismo tenant
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant"),
    )

    def __repr__(self) -> str:
        return f"<UserTenant(user={self.user_id}, tenant={self.tenant_id}, role={self.role})>"
