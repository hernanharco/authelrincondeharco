"""
Modelo CompanyProfile.
Datos maestros de la empresa asociada a un usuario.
1 usuario = 1 empresa (relación uno a uno).
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.models.base import Base


class CompanyProfile(Base):
    """
    Perfil de empresa del usuario.
    Contiene los datos maestros que otros proyectos consumen vía API o JWT.
    """

    __tablename__ = "company_profiles"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        autoincrement=True,
        comment="ID único autoincremental",
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # 1 usuario = 1 empresa
        nullable=False,
        comment="FK al usuario propietario de esta empresa",
    )

    company_name = Column(
        String(255),
        nullable=False,
        comment="Nombre legal de la empresa",
    )

    cif = Column(
        String(20),
        nullable=True,
        comment="CIF / NIF de la empresa",
    )

    address = Column(
        Text,
        nullable=True,
        comment="Dirección fiscal de la empresa",
    )

    iban = Column(
        String(34),
        nullable=True,
        comment="IBAN para pagos/transferencias",
    )

    phone = Column(
        String(20),
        nullable=True,
        comment="Teléfono de contacto de la empresa",
    )

    contact_name = Column(
        String(255),
        nullable=True,
        comment="Nombre del dueño o persona de contacto",
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

    # Relación con User (opcional, para navegación ORM)
    user = relationship("User", backref="company_profile", uselist=False)

    def __repr__(self) -> str:
        return f"<CompanyProfile(id={self.id}, company='{self.company_name}')>"
