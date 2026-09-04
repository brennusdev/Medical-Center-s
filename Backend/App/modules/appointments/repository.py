"""MED V2 — Data access layer for appointments (no business rules here)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from App.modules.appointments.models import Appointment, AppointmentRequest


class AppointmentRequestRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, request: AppointmentRequest) -> AppointmentRequest:
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get(self, request_id: int) -> AppointmentRequest | None:
        return self.db.get(AppointmentRequest, request_id)

    def list_by_patient(self, patient_id: int) -> list[AppointmentRequest]:
        stmt = (
            select(AppointmentRequest)
            .where(AppointmentRequest.patient_id == patient_id)
            .order_by(AppointmentRequest.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())


class AppointmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment

    def get(self, appointment_id: int) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def list_by_patient(self, patient_id: int) -> list[Appointment]:
        stmt = (
            select(Appointment)
            .where(Appointment.patient_id == patient_id)
            .order_by(Appointment.scheduled_at)
        )
        return list(self.db.scalars(stmt).all())

    def next_for_patient(self, patient_id: int, now: datetime) -> Appointment | None:
        stmt = (
            select(Appointment)
            .where(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_at >= now,
            )
            .order_by(Appointment.scheduled_at)
            .limit(1)
        )
        return self.db.scalars(stmt).first()
