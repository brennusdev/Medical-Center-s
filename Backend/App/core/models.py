"""Central model registry — imported by Alembic so migrations see all tables."""

from App.core.database import Base  # noqa: F401
from App.modules.appointments.models import (  # noqa: F401
    Appointment,
    AppointmentRequest,
    AppointmentStatus,
    RequestStatus,
)
from App.modules.users.models import User  # noqa: F401

__all__ = [
    "Base",
    "Appointment",
    "AppointmentRequest",
    "AppointmentStatus",
    "RequestStatus",
    "User",
]
