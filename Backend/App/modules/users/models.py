"""MED V1 (users domain) — kept as-is; appointments reference patients by id."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from App.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # MED V3 (aditivo): papel do usuário. Default PATIENT preserva a V1/V2.
    # V9: perfis de segurança PATIENT/DOCTOR/HOSPITAL/ADMIN (+ legados
    # RECEPTIONIST/NURSE da V4, mantidos para não quebrar nada existente).
    role: Mapped[str] = mapped_column(String(20), default="PATIENT", server_default="PATIENT", nullable=False)
    # V9 (aditivo, nullable): hash da senha no formato do auth/security.py.
    # Nullable preserva usuários criados antes da V9 (migram no primeiro login
    # via fluxo de redefinição — nunca backfill de senha inventada).
    # Nunca armazenar a senha em texto puro neste campo.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
