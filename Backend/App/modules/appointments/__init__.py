"""MED V2 — Appointments and scheduling domain."""

from App.modules.appointments.models import Appointment, AppointmentRequest
from App.modules.appointments.router import router

__all__ = ["Appointment", "AppointmentRequest", "router"]
