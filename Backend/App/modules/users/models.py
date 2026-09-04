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
    role: Mapped[str] = mapped_column(String(20), default="PATIENT", server_default="PATIENT", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
