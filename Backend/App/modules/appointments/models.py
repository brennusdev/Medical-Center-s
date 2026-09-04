"""MED V2 — SQLAlchemy models for appointments and scheduling."""

import enum
from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from App.core.database import Base


class RequestStatus(str, enum.Enum):
    """Status of an appointment request."""

    REQUESTED = "REQUESTED"
    IN_REVIEW = "IN_REVIEW"
    SCHEDULED = "SCHEDULED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class AppointmentStatus(str, enum.Enum):
    """Status of a scheduled appointment."""

    SCHEDULED = "SCHEDULED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


class AppointmentRequest(Base):
    """Patient request for an appointment (MED V2)."""

    __tablename__ = "appointment_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int] = mapped_column(index=True, nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_date: Mapped[date] = mapped_column(Date, nullable=False)
    preferred_time: Mapped[time] = mapped_column(Time, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status"),
        default=RequestStatus.REQUESTED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="request")


class Appointment(Base):
    """Scheduled appointment (MED V2)."""

    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        ForeignKey("appointment_requests.id"), index=True, nullable=False
    )
    patient_id: Mapped[int] = mapped_column(index=True, nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    doctor_name: Mapped[str] = mapped_column(String(150), nullable=False)
    hospital_name: Mapped[str] = mapped_column(String(150), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    notes: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    request: Mapped["AppointmentRequest"] = relationship(back_populates="appointments")
