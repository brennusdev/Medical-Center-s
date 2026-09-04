"""MED V2 — Business rules for appointments and scheduling.

Rules stay here (never in router or repository):
- patient_id must be a positive integer;
- an appointment can only be created from an existing, active request;
- scheduled_at must be in the future;
- scheduling a request moves it to SCHEDULED.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from App.modules.appointments.models import (
    Appointment,
    AppointmentRequest,
    AppointmentStatus,
    RequestStatus,
)
from App.modules.appointments.repository import (
    AppointmentRepository,
    AppointmentRequestRepository,
)
from App.modules.appointments.schemas import AppointmentCreate, AppointmentRequestCreate

REQUEST_STATUSES_BLOCKING_SCHEDULING = {RequestStatus.CANCELLED, RequestStatus.EXPIRED, RequestStatus.SCHEDULED}


class NotFoundError(Exception):
    """Requested entity does not exist."""


class ValidationError(Exception):
    """Business rule violation."""


class AppointmentService:
    def __init__(self, db: Session, now: datetime | None = None) -> None:
        self.request_repo = AppointmentRequestRepository(db)
        self.appointment_repo = AppointmentRepository(db)
        self.now = now or datetime.now().astimezone()

    # -- Requests ----------------------------------------------------------
    def create_request(self, data: AppointmentRequestCreate) -> AppointmentRequest:
        if data.patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        request = AppointmentRequest(
            patient_id=data.patient_id,
            specialty=data.specialty.strip(),
            preferred_date=data.preferred_date,
            preferred_time=data.preferred_time,
            reason=data.reason.strip(),
            status=RequestStatus.REQUESTED,
        )
        return self.request_repo.create(request)

    def list_requests_by_patient(self, patient_id: int) -> list[AppointmentRequest]:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        return self.request_repo.list_by_patient(patient_id)

    # -- Appointments ------------------------------------------------------
    def create_appointment(self, data: AppointmentCreate) -> Appointment:
        request = self.request_repo.get(data.request_id)
        if request is None:
            raise NotFoundError(f"Solicitação {data.request_id} não encontrada")

        if request.status in REQUEST_STATUSES_BLOCKING_SCHEDULING:
            raise ValidationError(
                f"Solicitação {request.id} não pode ser agendada (status {request.status.value})"
            )

        if data.scheduled_at <= self.now:
            raise ValidationError("A consulta deve ser agendada para uma data/hora futura")

        appointment = Appointment(
            request_id=request.id,
            patient_id=request.patient_id,
            specialty=request.specialty,
            doctor_name=data.doctor_name.strip(),
            hospital_name=data.hospital_name.strip(),
            scheduled_at=data.scheduled_at,
            status=AppointmentStatus.SCHEDULED,
            notes=data.notes.strip(),
        )
        created = self.appointment_repo.create(appointment)

        request.status = RequestStatus.SCHEDULED
        self.request_repo.db.commit()
        self.request_repo.db.refresh(request)
        return created

    def list_appointments_by_patient(self, patient_id: int) -> list[Appointment]:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        return self.appointment_repo.list_by_patient(patient_id)

    def get_appointment(self, appointment_id: int) -> Appointment:
        appointment = self.appointment_repo.get(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Consulta {appointment_id} não encontrada")
        return appointment

    def next_appointment(self, patient_id: int) -> Appointment | None:
        if patient_id <= 0:
            raise ValidationError("patient_id deve ser um inteiro positivo")
        return self.appointment_repo.next_for_patient(patient_id, self.now)
