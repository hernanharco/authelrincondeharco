"""
Module model.
Define la estructura de la tabla modules en la base de datos.
Un module es un servicio funcional del SaaS (radar, inventory, etc.).
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.models.base import Base


class Module(Base):
    """
    Modelo ORM de la tabla modules.
    Responsabilidad única: representar la estructura de datos en la BD.
    """

    __tablename__ = "modules"

    id = Column(
        String(50),
        primary_key=True,
        comment="ID corto del módulo (radar, inventory)",
    )

    name = Column(
        String(255),
        nullable=False,
        comment="Nombre visible del módulo",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Descripción del módulo",
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Si está activo puede ser asignado a tenants",
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
        return f"<Module(id='{self.id}', name='{self.name}')>"
